#include "GurobiBaseline.hpp"

#include "CanonicalCompactModel.hpp"
#include "ControllingLeafScheduler.hpp"
#include "Evaluator.hpp"
#include "FileSha256.hpp"
#include "FixedIntervalMipBackend.hpp"
#include "GurobiCertificate.hpp"
#include "GurobiProgress.hpp"
#include "ProcessPhaseLedger.hpp"
#include "MipStartMapping.hpp"

#include <gurobi_c.h>

#include <algorithm>
#include <chrono>
#include <cctype>
#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <limits>
#include <memory>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace ebrp {
namespace {

using Clock = std::chrono::steady_clock;

#ifdef _WIN32

struct GurobiApi {
    HMODULE library = nullptr;
    decltype(&GRBloadenvinternal) loadenvinternal = nullptr;
    decltype(&GRBemptyenvinternal) emptyenvinternal = nullptr;
    decltype(&GRBstartenv) startenv = nullptr;
    decltype(&GRBfreeenv) freeenv = nullptr;
    decltype(&GRBgeterrormsg) geterrormsg = nullptr;
    decltype(&GRBversion) version = nullptr;
    decltype(&GRBreadmodel) readmodel = nullptr;
    decltype(&GRBfreemodel) freemodel = nullptr;
    decltype(&GRBgetenv) getenv = nullptr;
    decltype(&GRBsetintparam) setintparam = nullptr;
    decltype(&GRBsetdblparam) setdblparam = nullptr;
    decltype(&GRBsetstrparam) setstrparam = nullptr;
    decltype(&GRBgetintparam) getintparam = nullptr;
    decltype(&GRBgetdblparam) getdblparam = nullptr;
    decltype(&GRBsetcallbackfunc) setcallbackfunc = nullptr;
    decltype(&GRBcbget) cbget = nullptr;
    decltype(&GRBoptimize) optimize = nullptr;
    decltype(&GRBgetintattr) getintattr = nullptr;
    decltype(&GRBgetdblattr) getdblattr = nullptr;
    decltype(&GRBgetstrattrelement) getstrattrelement = nullptr;
    decltype(&GRBgetdblattrarray) getdblattrarray = nullptr;
    decltype(&GRBgetcharattrarray) getcharattrarray = nullptr;
    decltype(&GRBsetdblattrarray) setdblattrarray = nullptr;
    decltype(&GRBsetcharattrarray) setcharattrarray = nullptr;
    decltype(&GRBupdatemodel) updatemodel = nullptr;
    decltype(&GRBwrite) write = nullptr;
};

template <typename T>
bool resolve(HMODULE library, const char* name, T& target) {
    target = reinterpret_cast<T>(GetProcAddress(library, name));
    return target != nullptr;
}

std::string normalizedPath(const std::filesystem::path& path) {
    return path.lexically_normal().generic_string();
}

std::vector<std::filesystem::path> candidateRoots(
    const SolveOptions& options) {
    std::vector<std::filesystem::path> roots;
    if (!options.gurobi_home.empty()) roots.emplace_back(options.gurobi_home);
    if (const char* home = std::getenv("GUROBI_HOME")) {
        if (*home) roots.emplace_back(home);
    }
#ifdef EXACT_EBRP_GUROBI_ROOT
    roots.emplace_back(EXACT_EBRP_GUROBI_ROOT);
#endif
    // Discovery is version-neutral: scan only drive roots for Gurobi's
    // documented gurobi<version>/win64 layout.
    for (const char drive : std::string("CDEF")) {
        const std::filesystem::path root(
            std::string(1, drive) + ":/");
        std::error_code ec;
        if (!std::filesystem::exists(root, ec)) continue;
        for (const auto& entry : std::filesystem::directory_iterator(root, ec)) {
            if (ec || !entry.is_directory()) continue;
            std::string name = entry.path().filename().string();
            std::transform(name.begin(), name.end(), name.begin(),
                [](unsigned char ch) { return static_cast<char>(std::tolower(ch)); });
            if (name.rfind("gurobi", 0) != 0) continue;
            const std::filesystem::path win64 = entry.path() / "win64";
            if (std::filesystem::exists(win64 / "include" / "gurobi_c.h", ec)) {
                roots.push_back(win64);
            }
        }
    }
    std::vector<std::filesystem::path> unique;
    std::set<std::string> seen;
    for (const auto& root : roots) {
        std::filesystem::path normalized = root;
        if (normalized.filename() != "win64" &&
            std::filesystem::exists(normalized / "win64")) {
            normalized /= "win64";
        }
        const std::string key = normalizedPath(normalized);
        if (seen.insert(key).second) unique.push_back(normalized);
    }
    return unique;
}

std::filesystem::path findNativeLibrary(
    const SolveOptions& options,
    std::filesystem::path* installation_root) {
    for (const auto& root : candidateRoots(options)) {
        const std::filesystem::path bin = root / "bin";
        std::error_code ec;
        if (!std::filesystem::exists(bin, ec)) continue;
        std::vector<std::filesystem::path> candidates;
        for (const auto& entry : std::filesystem::directory_iterator(bin, ec)) {
            if (ec || !entry.is_regular_file()) continue;
            std::string name = entry.path().filename().string();
            std::transform(name.begin(), name.end(), name.begin(),
                [](unsigned char ch) { return static_cast<char>(std::tolower(ch)); });
            if (name.rfind("gurobi", 0) == 0 &&
                name.size() > 10 && name.substr(name.size() - 4) == ".dll" &&
                name.find("_light") == std::string::npos &&
                name.find(".net") == std::string::npos &&
                name.find("jni") == std::string::npos) {
                candidates.push_back(entry.path());
            }
        }
        std::sort(candidates.begin(), candidates.end());
        if (!candidates.empty()) {
            if (installation_root) *installation_root = root;
            return candidates.back();
        }
    }
    return {};
}

bool loadGurobiApi(const SolveOptions& options,
                   GurobiApi& api,
                   std::filesystem::path& root,
                   std::filesystem::path& library_path,
                   std::string& reason) {
    library_path = findNativeLibrary(options, &root);
    if (library_path.empty()) {
        reason = "gurobi_native_library_not_found";
        return false;
    }
    api.library = LoadLibraryW(library_path.wstring().c_str());
    if (!api.library) {
        reason = "LoadLibrary_failed:" + std::to_string(GetLastError());
        return false;
    }
#define LOAD_GRB(member, symbol) \
    if (!resolve(api.library, symbol, api.member)) { \
        reason = std::string("missing_gurobi_symbol:") + symbol; \
        FreeLibrary(api.library); \
        api.library = nullptr; \
        return false; \
    }
    LOAD_GRB(loadenvinternal, "GRBloadenvinternal");
    LOAD_GRB(emptyenvinternal, "GRBemptyenvinternal");
    LOAD_GRB(startenv, "GRBstartenv");
    LOAD_GRB(freeenv, "GRBfreeenv");
    LOAD_GRB(geterrormsg, "GRBgeterrormsg");
    LOAD_GRB(version, "GRBversion");
    LOAD_GRB(readmodel, "GRBreadmodel");
    LOAD_GRB(freemodel, "GRBfreemodel");
    LOAD_GRB(getenv, "GRBgetenv");
    LOAD_GRB(setintparam, "GRBsetintparam");
    LOAD_GRB(setdblparam, "GRBsetdblparam");
    LOAD_GRB(setstrparam, "GRBsetstrparam");
    LOAD_GRB(getintparam, "GRBgetintparam");
    LOAD_GRB(getdblparam, "GRBgetdblparam");
    LOAD_GRB(setcallbackfunc, "GRBsetcallbackfunc");
    LOAD_GRB(cbget, "GRBcbget");
    LOAD_GRB(optimize, "GRBoptimize");
    LOAD_GRB(getintattr, "GRBgetintattr");
    LOAD_GRB(getdblattr, "GRBgetdblattr");
    LOAD_GRB(getstrattrelement, "GRBgetstrattrelement");
    LOAD_GRB(getdblattrarray, "GRBgetdblattrarray");
    LOAD_GRB(getcharattrarray, "GRBgetcharattrarray");
    LOAD_GRB(setdblattrarray, "GRBsetdblattrarray");
    LOAD_GRB(setcharattrarray, "GRBsetcharattrarray");
    LOAD_GRB(updatemodel, "GRBupdatemodel");
    LOAD_GRB(write, "GRBwrite");
#undef LOAD_GRB
    reason = "loaded";
    return true;
}

std::string apiError(const GurobiApi& api, GRBenv* env, int code) {
    std::ostringstream out;
    out << "gurobi_error_" << code;
    if (env && api.geterrormsg) {
        const char* message = api.geterrormsg(env);
        if (message && *message) {
            const std::string text(message);
            // Error 10009 may append user, host, and host-id licensing
            // metadata.  Preserve the actionable class without serializing
            // machine-bound license-identifying details.
            if (code == 10009 &&
                text.find("No Gurobi license found") != std::string::npos) {
                out << ":No Gurobi license found";
            } else {
                out << ':' << text;
            }
        }
    }
    return out.str();
}

int startSilentGurobiEnvironment(
    const GurobiApi& api,
    GRBenv** env,
    const std::filesystem::path& post_license_log = {}) {
    if (!env) return GRB_ERROR_NULL_ARGUMENT;
    *env = nullptr;
    int rc = api.emptyenvinternal(
        env, GRB_VERSION_MAJOR, GRB_VERSION_MINOR,
        GRB_VERSION_TECHNICAL);
    if (rc != 0 || !*env) return rc;
    rc = api.setintparam(*env, GRB_INT_PAR_LOGTOCONSOLE, 0);
    if (rc != 0) return rc;
    // No log target is active while GRBstartenv acquires the license.  This
    // prevents machine-bound license identifiers from entering console or
    // evidence logs.  Native solve logging begins only after startup.
    rc = api.startenv(*env);
    if (rc != 0) return rc;
    if (!post_license_log.empty()) {
        if (post_license_log.has_parent_path()) {
            std::filesystem::create_directories(
                post_license_log.parent_path());
        }
        rc = api.setstrparam(
            *env, GRB_STR_PAR_LOGFILE, post_license_log.string().c_str());
    }
    return rc;
}

struct ProgressCallbackState {
    GurobiApi* api = nullptr;
    GurobiProgressStats progress;
    double last_record_time = -1.0;
    double last_incumbent = std::numeric_limits<double>::infinity();
    double last_bound = -std::numeric_limits<double>::infinity();
};

bool finiteNative(double value) {
    return std::isfinite(value) && std::fabs(value) < GRB_INFINITY;
}

int __stdcall readOnlyProgressCallback(
    GRBmodel*, void* cbdata, int where, void* usrdata) {
    auto* state = static_cast<ProgressCallbackState*>(usrdata);
    if (!state || !state->api || where != GRB_CB_MIP) return 0;
    ++state->progress.callback_invocations;
    GurobiProgressEvent event;
    event.callback_where = where;
    event.context = "MIP";
    if (state->api->cbget(cbdata, where, GRB_CB_RUNTIME,
                          &event.elapsed_runtime_seconds) != 0) return 0;
    state->api->cbget(cbdata, where, GRB_CB_WORK, &event.work);
    state->api->cbget(cbdata, where, GRB_CB_MIP_OBJBST, &event.incumbent);
    state->api->cbget(cbdata, where, GRB_CB_MIP_OBJBND, &event.best_bound);
    state->api->cbget(cbdata, where, GRB_CB_MIP_NODCNT,
                      &event.processed_nodes);
    state->api->cbget(cbdata, where, GRB_CB_MIP_NODLFT, &event.open_nodes);
    state->api->cbget(cbdata, where, GRB_CB_MIP_SOLCNT,
                      &event.solution_count);
    state->api->cbget(cbdata, where, GRB_CB_MIP_PHASE, &event.phase);
    event.incumbent_available = finiteNative(event.incumbent);
    event.best_bound_available = finiteNative(event.best_bound);
    if (event.incumbent_available &&
        state->progress.first_incumbent_time < 0.0) {
        state->progress.first_incumbent_time = event.elapsed_runtime_seconds;
    }
    const bool bound_improved = event.best_bound_available &&
        (!std::isfinite(state->last_bound) ||
         event.best_bound > state->last_bound +
            1e-12 * std::max(1.0, std::fabs(state->last_bound)));
    const bool incumbent_improved = event.incumbent_available &&
        (!std::isfinite(state->last_incumbent) ||
         event.incumbent < state->last_incumbent -
            1e-12 * std::max(1.0, std::fabs(state->last_incumbent)));
    if (bound_improved) {
        state->last_bound = event.best_bound;
        state->progress.last_lower_bound_improvement_time =
            event.elapsed_runtime_seconds;
    }
    const bool changed = incumbent_improved || bound_improved;
    if (event.incumbent_available) {
        state->last_incumbent =
            std::min(state->last_incumbent, event.incumbent);
    }
    if (state->last_record_time < 0.0 || changed ||
        event.elapsed_runtime_seconds >= state->last_record_time + 0.1) {
        try {
            state->progress.events.push_back(event);
            ++state->progress.records;
            state->last_record_time = event.elapsed_runtime_seconds;
        } catch (...) {
            ++state->progress.dropped_records;
        }
    }
    return 0;
}

std::string versionString(const GurobiApi& api) {
    int major = 0;
    int minor = 0;
    int technical = 0;
    api.version(&major, &minor, &technical);
    return std::to_string(major) + "." + std::to_string(minor) + "." +
        std::to_string(technical);
}

std::string headerVersionString() {
    return std::to_string(GRB_VERSION_MAJOR) + "." +
        std::to_string(GRB_VERSION_MINOR) + "." +
        std::to_string(GRB_VERSION_TECHNICAL);
}

struct GurobiNativeLogEvidence {
    bool available = false;
    bool presolve_executed = false;
    bool root_relaxation_executed = false;
    bool explicit_continuation = false;
    bool explicit_incumbent_reuse = false;
    bool mip_start_accepted = false;
    bool mip_start_rejected = false;
    bool mip_start_no_incumbent = false;
};

GurobiNativeLogEvidence inspectGurobiNativeLog(
    const std::filesystem::path& path) {
    GurobiNativeLogEvidence out;
    std::ifstream input(path, std::ios::binary);
    if (!input) return out;
    out.available = true;
    std::ostringstream buffer;
    buffer << input.rdbuf();
    std::string text = buffer.str();
    std::transform(text.begin(), text.end(), text.begin(),
        [](unsigned char ch) { return static_cast<char>(std::tolower(ch)); });
    out.presolve_executed = text.find("presolve removed") != std::string::npos ||
        text.find("presolve time") != std::string::npos ||
        text.find("presolved:") != std::string::npos;
    out.root_relaxation_executed =
        text.find("root relaxation:") != std::string::npos;
    // These classifications deliberately require affirmative native text.
    // Repeated Optimize calls and monotone-looking attributes are not proof
    // that a native search tree continued.
    out.explicit_continuation =
        text.find("continuing previous optimization") != std::string::npos ||
        text.find("resuming previous optimization") != std::string::npos;
    out.explicit_incumbent_reuse =
        text.find("loaded incumbent from previous solve") != std::string::npos;
    out.mip_start_accepted =
        text.find("loaded user mip start with objective") != std::string::npos;
    out.mip_start_rejected =
        text.find("user mip start violates constraint") != std::string::npos ||
        text.find("user mip start is infeasible") != std::string::npos;
    out.mip_start_no_incumbent =
        text.find("user mip start did not produce a new incumbent solution") !=
            std::string::npos;
    return out;
}

struct CanonicalLpVariableAudit {
    struct Variable {
        double lower = 0.0;
        double upper = GRB_INFINITY;
        char type = GRB_CONTINUOUS;
    };
    bool parsed = false;
    int objective_sense = 0;
    std::unordered_map<std::string, Variable> variables;
    std::string failure_reason = "not_parsed";
};

CanonicalLpVariableAudit parseCanonicalLpVariableAudit(
    const std::filesystem::path& path) {
    CanonicalLpVariableAudit out;
    std::ifstream input(path);
    if (!input) {
        out.failure_reason = "canonical_lp_open_failed";
        return out;
    }
    enum class Section { Header, Bounds, Generals, Binaries, Done };
    Section section = Section::Header;
    std::string line;
    while (std::getline(input, line)) {
        if (line == "Minimize") { out.objective_sense = 1; continue; }
        if (line == "Maximize") { out.objective_sense = -1; continue; }
        if (line == "Bounds") { section = Section::Bounds; continue; }
        if (line == "Generals") { section = Section::Generals; continue; }
        if (line == "Binaries") { section = Section::Binaries; continue; }
        if (line == "End") { section = Section::Done; break; }
        if (line.empty() || line.front() == '\\') continue;
        std::istringstream fields(line);
        if (section == Section::Bounds) {
            double lower = 0.0, upper = 0.0;
            std::string lower_op, name, upper_op;
            if (!(fields >> lower >> lower_op >> name >> upper_op >> upper) ||
                lower_op != "<=" || upper_op != "<=") {
                out.failure_reason = "unsupported_canonical_bound_line";
                return out;
            }
            out.variables[name] = {lower, upper, GRB_CONTINUOUS};
        } else if (section == Section::Generals ||
                   section == Section::Binaries) {
            std::string name;
            if (!(fields >> name)) continue;
            auto found = out.variables.find(name);
            if (found == out.variables.end()) {
                out.failure_reason = "typed_variable_missing_bound:" + name;
                return out;
            }
            found->second.type = section == Section::Generals
                ? GRB_INTEGER : GRB_BINARY;
        }
    }
    if (out.objective_sense == 0 || out.variables.empty() ||
        section != Section::Done) {
        out.failure_reason = "canonical_lp_required_sections_missing";
        return out;
    }
    out.parsed = true;
    out.failure_reason = "none";
    return out;
}

class GurobiFixedIntervalBackend final : public FixedIntervalMipBackend {
public:
    GurobiFixedIntervalBackend(const Instance& instance,
                               const SolveOptions& options)
        : instance_(instance), options_(options) {
        std::filesystem::path root;
        std::filesystem::path library;
        if (!loadGurobiApi(options_, api_, root, library, failure_reason_)) {
            return;
        }
        installation_root_ = normalizedPath(root);
        library_path_ = normalizedPath(library);
        std::filesystem::path log = options_.log_path.empty()
            ? std::filesystem::path("results") / "gurobi_work" /
                "external_gini_backend.log"
            : std::filesystem::path(options_.log_path);
        if (log.has_parent_path()) {
            std::filesystem::create_directories(log.parent_path());
        }
        const int rc = startSilentGurobiEnvironment(api_, &env_, log);
        recordProcessPhase(
            options_, "gurobi_environment_creation",
            (rc == 0 && env_) ? "complete" : "failed",
            "fixed_interval_backend");
        if (rc != 0 || !env_) {
            failure_reason_ = apiError(api_, env_, rc);
            if (env_) api_.freeenv(env_);
            env_ = nullptr;
            if (api_.library) FreeLibrary(api_.library);
            api_.library = nullptr;
            return;
        }
        ++stats_.environment_count;
        const int threads_rc = api_.setintparam(env_, GRB_INT_PAR_THREADS, 1);
        const int presolve_rc = api_.setintparam(
            env_, GRB_INT_PAR_PRESOLVE, options_.gurobi_presolve);
        const int seed_rc = api_.setintparam(
            env_, GRB_INT_PAR_SEED, options_.gurobi_seed);
        const int rel_rc = api_.setdblparam(env_, GRB_DBL_PAR_MIPGAP, 0.0);
        const int abs_rc = api_.setdblparam(env_, GRB_DBL_PAR_MIPGAPABS, 0.0);
        int threads = 0, presolve = -99, seed = -1;
        double rel = -1.0, abs = -1.0;
        const bool readbacks =
            api_.getintparam(env_, GRB_INT_PAR_THREADS, &threads) == 0 &&
            api_.getintparam(env_, GRB_INT_PAR_PRESOLVE, &presolve) == 0 &&
            api_.getintparam(env_, GRB_INT_PAR_SEED, &seed) == 0 &&
            api_.getdblparam(env_, GRB_DBL_PAR_MIPGAP, &rel) == 0 &&
            api_.getdblparam(env_, GRB_DBL_PAR_MIPGAPABS, &abs) == 0;
        configuration_valid_ = threads_rc == 0 && presolve_rc == 0 &&
            seed_rc == 0 && rel_rc == 0 && abs_rc == 0 && readbacks &&
            threads == 1 && presolve == options_.gurobi_presolve &&
            seed == options_.gurobi_seed && rel == 0.0 && abs == 0.0;
        if (!configuration_valid_) {
            failure_reason_ = "gurobi_external_parameter_roundtrip_failed";
            return;
        }
        available_ = true;
        failure_reason_ = "none";
    }

    ~GurobiFixedIntervalBackend() override {
        release();
    }

    void release() override {
        for (auto& item : leaves_) {
            if (item.second.model) {
                api_.freemodel(item.second.model);
                item.second.model = nullptr;
                ++stats_.model_free_count;
            }
        }
        leaves_.clear();
        if (env_) {
            api_.freeenv(env_);
            env_ = nullptr;
            ++stats_.environment_free_count;
        }
        if (api_.library) {
            FreeLibrary(api_.library);
            api_.library = nullptr;
        }
    }

    void discardLeaf(const std::string& leaf_id) override {
        const auto found = leaves_.find(leaf_id);
        if (found == leaves_.end()) return;
        if (found->second.model) {
            api_.freemodel(found->second.model);
            found->second.model = nullptr;
            ++stats_.model_free_count;
        }
        leaves_.erase(found);
        ++stats_.explicit_leaf_model_discard_count;
    }

    FixedIntervalMipCapabilities capabilities() const override {
        FixedIntervalMipCapabilities out;
        out.backend = "gurobi";
        out.available = available_;
        out.retained_same_leaf_resume = available_;
        out.fresh_per_attempt = true;
        out.verified_complete_mip_start = available_;
        out.native_continuation_evidence = false;
        out.exact_zero_gap_roundtrip = configuration_valid_;
        out.failure_reason = failure_reason_;
        return out;
    }

    FixedIntervalMipOutcome solve(
        const FixedIntervalMipRequest& request) override {
        FixedIntervalMipOutcome out;
        out.attempted = true;
        out.available = available_;
        out.presolve_time_status =
            "unavailable_gurobi_c_api_has_no_phase_timer_attribute";
        out.root_time_status =
            "unavailable_gurobi_c_api_has_no_phase_timer_attribute";
        if (!available_) {
            out.failure_reason = failure_reason_;
            return out;
        }
        const bool paper_solve =
            request.solve_kind != FixedIntervalSolveKind::LegacyMipQuantum;
        out.lp_relaxation =
            request.solve_kind == FixedIntervalSolveKind::PaperLpRelaxation;
        out.terminal_mip =
            request.solve_kind == FixedIntervalSolveKind::PaperTerminalMip;
        const bool legacy_retained_mode =
            !paper_solve &&
            options_.external_gini_lifecycle == "retained-per-leaf";
        auto found = leaves_.find(request.leaf_id);
        const bool incremental_retained_mode =
            paper_solve && request.incremental_model_reuse_enabled;
        bool retained =
            (legacy_retained_mode || incremental_retained_mode) &&
            found != leaves_.end();
        if (found != leaves_.end() && !retained) {
            if (found->second.model) {
                api_.freemodel(found->second.model);
                ++stats_.model_free_count;
            }
            leaves_.erase(found);
            found = leaves_.end();
        }
        if (retained &&
            found->second.model_fingerprint != request.canonical_model_fingerprint) {
            out.failure_reason = "retained_leaf_model_fingerprint_changed";
            return out;
        }

        if (!retained) {
            const auto read_started = Clock::now();
            LeafState state;
            const int read_rc = api_.readmodel(
                env_, request.canonical_model_path.string().c_str(),
                &state.model);
            const double read_seconds = std::chrono::duration<double>(
                Clock::now() - read_started).count();
            stats_.cumulative_model_read_seconds += read_seconds;
            out.model_read_seconds = read_seconds;
            if (read_rc != 0 || !state.model) {
                out.failure_reason = apiError(api_, env_, read_rc);
                return out;
            }
            state.model_fingerprint = request.canonical_model_fingerprint;
            state.new_child = request.new_leaf;
            ++stats_.model_count;
            ++stats_.model_read_count;
            if (!paper_solve) {
                ++stats_.fresh_restart_count;
                if (request.new_leaf) ++stats_.child_restart_count;
                out.fresh_restart = true;
                out.child_restart = request.new_leaf;
            }
            auto inserted = leaves_.emplace(request.leaf_id, std::move(state));
            found = inserted.first;
        } else {
            out.same_leaf_model_retained = true;
            ++stats_.same_leaf_resume_count;
            if (incremental_retained_mode) {
                out.in_memory_model_reused = true;
                ++stats_.in_memory_model_reuse_count;
            }
        }
        LeafState& state = found->second;
        GRBmodel* model = state.model;
        GRBenv* model_env = api_.getenv(model);
        if (!model_env) {
            out.failure_reason = "gurobi_external_model_environment_missing";
            return out;
        }
        if (out.lp_relaxation) {
            int variable_count = 0;
            if (api_.getintattr(model, GRB_INT_ATTR_NUMVARS,
                                &variable_count) != 0 || variable_count <= 0) {
                out.failure_reason = "paper_lp_variable_count_unavailable";
                return out;
            }
            if (request.incremental_model_reuse_enabled &&
                state.original_variable_types.empty()) {
                state.original_variable_types.resize(
                    static_cast<std::size_t>(variable_count));
                if (api_.getcharattrarray(
                        model, GRB_CHAR_ATTR_VTYPE, 0, variable_count,
                        state.original_variable_types.data()) != 0) {
                    state.original_variable_types.clear();
                    out.failure_reason =
                        "round29_original_integer_domain_capture_failed";
                    return out;
                }
            }
            std::vector<char> continuous(
                static_cast<std::size_t>(variable_count), GRB_CONTINUOUS);
            const int type_rc = api_.setcharattrarray(
                model, GRB_CHAR_ATTR_VTYPE, 0, variable_count,
                continuous.data());
            const int update_rc = type_rc == 0 ? api_.updatemodel(model)
                                                : type_rc;
            if (type_rc != 0 || update_rc != 0) {
                out.failure_reason = type_rc != 0
                    ? apiError(api_, model_env, type_rc)
                    : apiError(api_, model_env, update_rc);
                return out;
            }
            out.native_model_modified = true;
        }
        const double effective_limit = paper_solve
            ? request.global_deadline_remaining_seconds
            : request.time_limit_seconds;
        const int time_rc = api_.setdblparam(
            model_env, GRB_DBL_PAR_TIMELIMIT,
            std::max(0.001, effective_limit));
        out.native_log_path = request.native_log_path.string();
        int log_rc = 0;
        if (!request.native_log_path.empty()) {
            if (request.native_log_path.has_parent_path()) {
                std::filesystem::create_directories(
                    request.native_log_path.parent_path());
            }
            log_rc = api_.setstrparam(
                model_env, GRB_STR_PAR_LOGFILE,
                request.native_log_path.string().c_str());
        }
        double rel_gap = -1.0, abs_gap = -1.0;
        const int rel_get = api_.getdblparam(
            model_env, GRB_DBL_PAR_MIPGAP, &rel_gap);
        const int abs_get = api_.getdblparam(
            model_env, GRB_DBL_PAR_MIPGAPABS, &abs_gap);
        out.exact_zero_gap_roundtrip = configuration_valid_ && time_rc == 0 &&
            rel_get == 0 && abs_get == 0 && rel_gap == 0.0 && abs_gap == 0.0;
        out.model_fingerprint_matches_request =
            fileSha256(request.canonical_model_path) ==
                request.canonical_model_fingerprint;

        if (!retained && request.warm_start_enabled &&
            !request.verified_start_routes.empty()) {
            out.warm_start_candidate_available = true;
            ++stats_.warm_start_candidate_count;
            int nvars = 0;
            if (api_.getintattr(model, GRB_INT_ATTR_NUMVARS, &nvars) == 0 &&
                nvars > 0) {
                SolverNeutralModelDomain domain;
                domain.names.resize(static_cast<std::size_t>(nvars));
                domain.lower_bounds.resize(static_cast<std::size_t>(nvars));
                domain.upper_bounds.resize(static_cast<std::size_t>(nvars));
                domain.variable_types.resize(static_cast<std::size_t>(nvars));
                bool domain_ok = api_.getdblattrarray(
                    model, GRB_DBL_ATTR_LB, 0, nvars,
                    domain.lower_bounds.data()) == 0 &&
                    api_.getdblattrarray(model, GRB_DBL_ATTR_UB, 0, nvars,
                    domain.upper_bounds.data()) == 0 &&
                    api_.getcharattrarray(model, GRB_CHAR_ATTR_VTYPE, 0, nvars,
                    domain.variable_types.data()) == 0;
                for (int i = 0; domain_ok && i < nvars; ++i) {
                    char* name = nullptr;
                    domain_ok = api_.getstrattrelement(
                        model, GRB_STR_ATTR_VARNAME, i, &name) == 0 && name;
                    if (domain_ok) domain.names[static_cast<std::size_t>(i)] = name;
                }
                if (domain_ok) {
                    const SolverNeutralMipStart mapped =
                        mapVerifiedRoutesToCanonicalModel(
                            instance_, options_, request.verified_start_routes,
                            request.verified_start_source, request.gamma_L,
                            request.gamma_U, request.verified_cutoff, domain);
                    out.warm_start_mapping_seconds = mapped.mapping_seconds;
                    out.warm_start_mapping_complete = mapped.complete;
                    if (mapped.complete) {
                        ++stats_.warm_start_complete_count;
                        const int start_rc = api_.setdblattrarray(
                            model, GRB_DBL_ATTR_START, 0, nvars,
                            const_cast<double*>(mapped.values.data()));
                        out.warm_start_submitted = start_rc == 0;
                        if (out.warm_start_submitted) {
                            ++stats_.warm_start_submitted_count;
                            out.warm_start_status =
                                "submitted_pending_native_log_evidence";
                        } else {
                            ++stats_.warm_start_rejected_count;
                            out.warm_start_status = "rejected_on_submission";
                        }
                    } else {
                        ++stats_.warm_start_rejected_count;
                        out.warm_start_status =
                            "mapping_rejected:" + mapped.failure_reason;
                    }
                } else {
                    ++stats_.warm_start_rejected_count;
                    out.warm_start_status = "model_domain_read_failed";
                }
            }
        }

        ProgressCallbackState callback;
        callback.api = &api_;
        const int callback_rc = api_.setcallbackfunc(
            model, readOnlyProgressCallback, &callback);
        if (callback_rc != 0) {
            out.failure_reason = apiError(api_, model_env, callback_rc);
            return out;
        }
        out.optimize_return_code = api_.optimize(model);
        if (!request.native_log_path.empty()) {
            // Closing the per-attempt log target makes the evidence immutable
            // before it is classified or hashed by the experiment harness.
            api_.setstrparam(model_env, GRB_STR_PAR_LOGFILE, "");
        }
        ++stats_.optimize_count;
        if (out.lp_relaxation) ++stats_.lp_relaxation_optimize_count;
        if (out.terminal_mip) ++stats_.terminal_mip_optimize_count;
        ++state.optimize_count;
        out.solver_finalization_reached = out.optimize_return_code == 0;
        auto getInt = [&](const char* attr, int& target) {
            return api_.getintattr(model, attr, &target) == 0;
        };
        auto getDouble = [&](const char* attr, double& target) {
            return api_.getdblattr(model, attr, &target) == 0 &&
                std::isfinite(target);
        };
        getInt(GRB_INT_ATTR_STATUS, out.native_status_code);
        out.native_status = gurobiStatusName(out.native_status_code);
        out.optimal = out.native_status_code == GRB_OPTIMAL;
        out.native_exact_optimal = out.optimal;
        out.native_status_supported = out.native_status_code >= GRB_LOADED &&
            out.native_status_code <= GRB_MEM_LIMIT;
        out.infeasible = out.native_status_code == GRB_INFEASIBLE;
        out.interrupted = out.native_status_code == GRB_TIME_LIMIT ||
            out.native_status_code == GRB_NODE_LIMIT ||
            out.native_status_code == GRB_ITERATION_LIMIT ||
            out.native_status_code == GRB_SOLUTION_LIMIT ||
            out.native_status_code == GRB_INTERRUPTED ||
            out.native_status_code == GRB_WORK_LIMIT ||
            out.native_status_code == GRB_MEM_LIMIT;
        out.native_bound_available = getDouble(
            GRB_DBL_ATTR_OBJBOUNDC, out.native_bound);
        if (out.lp_relaxation && out.optimal) {
            double lp_objective = 0.0;
            if (getDouble(GRB_DBL_ATTR_OBJVAL, lp_objective)) {
                out.native_bound = lp_objective;
                out.native_bound_available = true;
            }
        }
        out.lp_terminal_valid = out.lp_relaxation &&
            out.solver_finalization_reached &&
            (out.optimal || out.infeasible) &&
            (out.infeasible || out.native_bound_available);
        double per_call_runtime = 0.0, per_call_work = 0.0,
               per_call_nodes = 0.0, per_call_iter = 0.0;
        getDouble(GRB_DBL_ATTR_RUNTIME, per_call_runtime);
        getDouble(GRB_DBL_ATTR_WORK, per_call_work);
        getDouble(GRB_DBL_ATTR_NODECOUNT, per_call_nodes);
        getDouble(GRB_DBL_ATTR_ITERCOUNT, per_call_iter);
        int bar_iter = 0;
        getInt(GRB_INT_ATTR_BARITERCOUNT, bar_iter);
        getDouble(GRB_DBL_ATTR_MAXMEMUSED, out.memory_gb);
        // Gurobi's work/runtime/node/iteration attributes describe the most
        // recent Optimize call.  Treat them as per-call values and maintain
        // our own explicit sums; never infer continuation from them.
        out.solver_runtime_seconds = std::max(0.0, per_call_runtime);
        out.work = std::max(0.0, per_call_work);
        out.nodes = std::max(0.0, per_call_nodes);
        out.simplex_iterations = std::max(0.0, per_call_iter);
        out.barrier_iterations = std::max(0.0, static_cast<double>(bar_iter));
        state.cumulative_runtime += out.solver_runtime_seconds;
        state.cumulative_work += out.work;
        state.cumulative_nodes += out.nodes;
        state.cumulative_iterations += out.simplex_iterations;
        state.cumulative_barrier_iterations += out.barrier_iterations;
        out.cumulative_runtime = state.cumulative_runtime;
        out.cumulative_work = state.cumulative_work;
        out.cumulative_nodes = state.cumulative_nodes;
        out.cumulative_simplex_iterations = state.cumulative_iterations;
        out.cumulative_barrier_iterations =
            state.cumulative_barrier_iterations;
        stats_.cumulative_solver_runtime_seconds += out.solver_runtime_seconds;
        stats_.cumulative_work += out.work;
        if (out.lp_relaxation) stats_.cumulative_lp_work += out.work;
        if (out.terminal_mip) {
            stats_.cumulative_terminal_mip_work += out.work;
        }
        stats_.cumulative_nodes += out.nodes;
        stats_.cumulative_simplex_iterations += out.simplex_iterations;
        stats_.cumulative_barrier_iterations += out.barrier_iterations;
        stats_.peak_memory_gb = std::max(stats_.peak_memory_gb, out.memory_gb);

        int solution_count = 0;
        getInt(GRB_INT_ATTR_SOLCOUNT, solution_count);
        const GurobiNativeLogEvidence log_evidence =
            inspectGurobiNativeLog(request.native_log_path);
        out.presolve_rerun_observed = log_evidence.presolve_executed;
        out.root_relaxation_rerun_observed =
            log_evidence.root_relaxation_executed;
        out.incumbent_state_reused = log_evidence.explicit_incumbent_reuse;
        if (out.presolve_rerun_observed) ++stats_.presolve_execution_count;
        if (out.root_relaxation_rerun_observed) {
            ++stats_.root_relaxation_execution_count;
        }
        if (retained) {
            if (log_evidence.explicit_continuation &&
                !out.presolve_rerun_observed &&
                !out.root_relaxation_rerun_observed) {
                out.retained_state_classification = "confirmed_continuation";
                out.native_continuation_evidence = true;
                out.native_continuation_claimed = true;
                ++stats_.confirmed_continuation_count;
            } else if (out.incumbent_state_reused) {
                out.retained_state_classification = "partial_state_reuse";
                ++stats_.partial_state_reuse_count;
            } else if (out.presolve_rerun_observed ||
                       out.root_relaxation_rerun_observed) {
                out.retained_state_classification = "fresh_restart";
                ++stats_.observed_fresh_restart_count;
            } else {
                out.retained_state_classification = "unavailable_or_ambiguous";
                ++stats_.ambiguous_retained_state_count;
            }
        } else {
            out.retained_state_classification = "fresh_model_restart";
        }
        if (out.warm_start_submitted) {
            if (log_evidence.mip_start_accepted) {
                out.warm_start_status = "accepted_by_native_log";
                ++stats_.warm_start_accepted_count;
            } else if (log_evidence.mip_start_rejected) {
                out.warm_start_status = "rejected_by_native_log";
                ++stats_.warm_start_rejected_count;
            } else if (log_evidence.mip_start_no_incumbent) {
                out.warm_start_status = "submitted_no_new_incumbent";
                ++stats_.warm_start_unknown_count;
            } else {
                out.warm_start_status = log_evidence.available
                    ? "submitted_native_acceptance_ambiguous"
                    : "submitted_native_log_unavailable";
                ++stats_.warm_start_unknown_count;
            }
        }
        if (!out.lp_relaxation && solution_count > 0) {
            int nvars = 0;
            if (getInt(GRB_INT_ATTR_NUMVARS, nvars) && nvars > 0) {
                std::vector<double> x(static_cast<std::size_t>(nvars));
                std::unordered_map<std::string, double> values;
                if (api_.getdblattrarray(
                        model, GRB_DBL_ATTR_X, 0, nvars, x.data()) == 0) {
                    for (int i = 0; i < nvars; ++i) {
                        char* name = nullptr;
                        if (api_.getstrattrelement(
                                model, GRB_STR_ATTR_VARNAME, i, &name) == 0 &&
                            name) {
                            values[name] = x[static_cast<std::size_t>(i)];
                        }
                    }
                    std::vector<RoutePlan> routes =
                        reconstructCanonicalCompactRoutes(instance_, values);
                    const Verification verification =
                        verifySolution(instance_, routes, options_.lambda);
                    if (verification.original_solution_feasible &&
                        verification.original_objective_recomputed &&
                        verification.errors.empty()) {
                        out.incumbent_available = true;
                        out.incumbent_independently_verified = true;
                        out.incumbent_objective = verification.objective;
                        out.incumbent_routes = std::move(routes);
                    }
                }
            }
        }
        if (out.infeasible && !request.verified_start_routes.empty()) {
            const Verification witness = verifySolution(
                instance_, request.verified_start_routes, options_.lambda);
            const bool contradicts = witness.original_solution_feasible &&
                witness.original_objective_recomputed && witness.errors.empty() &&
                witness.G >= request.gamma_L - 1e-9 &&
                witness.G <= request.gamma_U + 1e-9 &&
                witness.objective <= request.verified_cutoff + 1e-9;
            out.feasibility_consistency_gate = !contradicts;
        }
        state.had_incumbent = !out.lp_relaxation && solution_count > 0;
        bool domain_restore_ok = true;
        if (out.lp_relaxation &&
            request.incremental_model_reuse_enabled) {
            const int nvars =
                static_cast<int>(state.original_variable_types.size());
            const int restore_rc = nvars > 0
                ? api_.setcharattrarray(
                      model, GRB_CHAR_ATTR_VTYPE, 0, nvars,
                      state.original_variable_types.data())
                : -1;
            const int update_rc = restore_rc == 0
                ? api_.updatemodel(model) : restore_rc;
            out.integer_domain_restored =
                restore_rc == 0 && update_rc == 0;
            domain_restore_ok = out.integer_domain_restored;
            if (out.integer_domain_restored) {
                ++stats_.integer_domain_restore_count;
                out.basis_reuse_status =
                    "not_submitted_domain_transition_model_object_only";
            } else {
                out.lp_terminal_valid = false;
            }
        }
        if (!out.solver_finalization_reached ||
            !out.exact_zero_gap_roundtrip ||
            !out.model_fingerprint_matches_request ||
            !out.feasibility_consistency_gate || !domain_restore_ok ||
            log_rc != 0) {
            std::ostringstream reason;
            reason << "gurobi_external_gate:finalized="
                   << out.solver_finalization_reached
                   << ";exact_zero_gaps=" << out.exact_zero_gap_roundtrip
                   << ";model_match=" << out.model_fingerprint_matches_request
                   << ";retained=" << retained
                   << ";continuation_evidence="
                   << out.native_continuation_evidence
                   << ";feasibility_consistency="
                   << out.feasibility_consistency_gate
                   << ";integer_domain_restored=" << domain_restore_ok
                   << ";native_log_parameter_rc=" << log_rc;
            out.failure_reason = reason.str();
        } else {
            out.failure_reason = "none";
        }
        if (paper_solve && !request.retain_model_after_solve) {
            out.retained_state_classification =
                out.in_memory_model_reused
                    ? "round29_same_leaf_model_reused_then_released"
                    : "paper_fresh_event_model";
            if (state.model) {
                api_.freemodel(state.model);
                state.model = nullptr;
                ++stats_.model_free_count;
            }
            leaves_.erase(request.leaf_id);
        } else if (paper_solve) {
            out.retained_state_classification =
                "round29_same_leaf_model_retained_no_basis_claim";
        }
        return out;
    }

    FixedIntervalMipBackendStats stats() const override { return stats_; }

private:
    struct LeafState {
        GRBmodel* model = nullptr;
        std::string model_fingerprint;
        bool new_child = false;
        int optimize_count = 0;
        bool had_incumbent = false;
        double cumulative_runtime = 0.0;
        double cumulative_work = 0.0;
        double cumulative_nodes = 0.0;
        double cumulative_iterations = 0.0;
        double cumulative_barrier_iterations = 0.0;
        std::vector<char> original_variable_types;
    };

    const Instance& instance_;
    SolveOptions options_;
    GurobiApi api_;
    GRBenv* env_ = nullptr;
    bool available_ = false;
    bool configuration_valid_ = false;
    std::string failure_reason_ = "not_initialized";
    std::string installation_root_;
    std::string library_path_;
    std::unordered_map<std::string, LeafState> leaves_;
    FixedIntervalMipBackendStats stats_;
};

#endif // _WIN32

} // namespace

bool gurobiBackendBuildEnabled() {
    return true;
}

GurobiRuntimeProbe probeGurobiRuntime(const SolveOptions& options) {
    GurobiRuntimeProbe probe;
    probe.build_enabled = true;
#ifdef _WIN32
    GurobiApi api;
    std::filesystem::path root;
    std::filesystem::path library;
    std::string reason;
    if (!loadGurobiApi(options, api, root, library, reason)) {
        probe.failure_reason = reason;
        return probe;
    }
    probe.runtime_library_found = true;
    probe.required_symbols_found = true;
    probe.installation_root = normalizedPath(root);
    probe.library_path = normalizedPath(library);
    probe.header_version = headerVersionString();
    probe.runtime_version = versionString(api);
    GRBenv* env = nullptr;
    probe.license_return_code = startSilentGurobiEnvironment(api, &env);
    probe.license_available = probe.license_return_code == 0 && env != nullptr;
    if (!probe.license_available) {
        probe.failure_reason = apiError(api, env, probe.license_return_code);
    } else {
        probe.failure_reason = "none";
    }
    if (env) api.freeenv(env);
    FreeLibrary(api.library);
    return probe;
#else
    (void)options;
    probe.failure_reason = "gurobi_dynamic_backend_requires_windows";
    return probe;
#endif
}

SolveResult solveGurobiBaseline(const Instance& instance,
                                const SolveOptions& options) {
    const auto start = Clock::now();
    SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "gurobi";
    result.status = "running";
    result.certificate = "not_certified";
    result.time_budget_seconds = options.solve_time_limit;
    result.gurobi_build_enabled = true;
    result.gurobi_header_version =
#ifdef _WIN32
        headerVersionString();
#else
        "unavailable";
#endif
    result.gurobi_threads_requested = 1;
    result.gurobi_presolve_requested = options.gurobi_presolve;
    result.gurobi_seed_requested = options.gurobi_seed;
    result.gurobi_mip_gap_requested = 0.0;
    result.gurobi_mip_gap_abs_requested = 0.0;
    result.solver_thread_policy = "plain_gurobi_single_thread";
    result.thread_fairness_class = "one_thread_fair";
    result.strict_certificate_policy_version =
        "round24-gurobi-engineering-exact-v1";

    try {
        const auto run_id = std::chrono::duration_cast<std::chrono::milliseconds>(
            Clock::now().time_since_epoch()).count();
        const std::string stem =
            std::filesystem::path(instance.name).stem().string() + "_plain";
        const std::filesystem::path work_dir =
            std::filesystem::path("results") / "gurobi_work" /
            (stem + "_" + std::to_string(run_id));
        std::filesystem::create_directories(work_dir);
        const std::filesystem::path lp_path =
            options.gurobi_model_export_path.empty()
                ? work_dir / "model.lp"
                : std::filesystem::path(options.gurobi_model_export_path);
        const std::filesystem::path log_path = options.log_path.empty()
            ? work_dir / "gurobi.log" : std::filesystem::path(options.log_path);
        const std::filesystem::path progress_path =
            options.gurobi_progress_path.empty()
                ? work_dir / "gurobi.progress.csv"
                : std::filesystem::path(options.gurobi_progress_path);
        if (log_path.has_parent_path()) {
            std::filesystem::create_directories(log_path.parent_path());
        }
        result.log_file = log_path.string();
        result.gurobi_progress_path = progress_path.string();

        // P-GRB is unconditionally plain.  It never consults a Tailored seed
        // or a caller's strengthened-model switch.
        CanonicalCompactModelSpec spec;
        spec.strengthened = false;
        const CanonicalCompactModelArtifact canonical =
            writeCanonicalCompactModel(instance, options, lp_path, spec);
        if (!canonical.written) {
            throw std::runtime_error(
                "canonical compact model write failed: " +
                canonical.failure_reason);
        }
        result.gurobi_canonical_model_sha256 = canonical.sha256;

#ifdef _WIN32
        GurobiApi api;
        std::filesystem::path installation_root;
        std::filesystem::path library_path;
        std::string load_reason;
        if (!loadGurobiApi(options, api, installation_root, library_path,
                            load_reason)) {
            result.status = "backend_unavailable";
            result.gurobi_failure_reason = load_reason;
            result.strict_certificate_class = "certificate_rejected";
            result.strict_certificate_rejection_reason = load_reason;
            result.runtime_seconds =
                std::chrono::duration<double>(Clock::now() - start).count();
            result.wall_time_seconds = result.runtime_seconds;
            return result;
        }
        result.gurobi_runtime_library_found = true;
        result.gurobi_installation_root = normalizedPath(installation_root);
        result.gurobi_native_library = library_path.filename().string();
        result.gurobi_version = versionString(api);

        GRBenv* env = nullptr;
        GRBmodel* model = nullptr;
        int model_free_rc = -1;
        auto cleanup = [&]() {
            if (model) {
                model_free_rc = api.freemodel(model);
                model = nullptr;
                ++result.gurobi_model_free_count;
            }
            if (env) {
                api.freeenv(env);
                env = nullptr;
                ++result.gurobi_environment_free_count;
            }
            if (api.library) {
                FreeLibrary(api.library);
                api.library = nullptr;
            }
        };

        const int env_rc = startSilentGurobiEnvironment(
            api, &env, log_path);
        result.gurobi_environment_creation_return_code = env_rc;
        if (env_rc != 0 || !env) {
            result.status = "license_unavailable";
            result.gurobi_license_available = false;
            result.gurobi_failure_reason = apiError(api, env, env_rc);
            result.strict_certificate_class = "certificate_rejected";
            result.strict_certificate_rejection_reason =
                "gurobi_license_unavailable:" + result.gurobi_failure_reason;
            cleanup();
            result.runtime_seconds =
                std::chrono::duration<double>(Clock::now() - start).count();
            result.wall_time_seconds = result.runtime_seconds;
            return result;
        }
        ++result.gurobi_environment_count;
        result.gurobi_license_available = true;

        result.gurobi_threads_set_return_code =
            api.setintparam(env, GRB_INT_PAR_THREADS, 1);
        result.gurobi_presolve_set_return_code =
            api.setintparam(env, GRB_INT_PAR_PRESOLVE,
                            options.gurobi_presolve);
        result.gurobi_seed_set_return_code =
            api.setintparam(env, GRB_INT_PAR_SEED, options.gurobi_seed);
        result.gurobi_mip_gap_set_return_code =
            api.setdblparam(env, GRB_DBL_PAR_MIPGAP, 0.0);
        result.gurobi_mip_gap_abs_set_return_code =
            api.setdblparam(env, GRB_DBL_PAR_MIPGAPABS, 0.0);
        int time_limit_rc = api.setdblparam(
            env, GRB_DBL_PAR_TIMELIMIT,
            std::max(0.001, options.solve_time_limit));
        result.gurobi_threads_get_return_code =
            api.getintparam(env, GRB_INT_PAR_THREADS,
                            &result.gurobi_threads_effective);
        result.gurobi_presolve_get_return_code =
            api.getintparam(env, GRB_INT_PAR_PRESOLVE,
                            &result.gurobi_presolve_effective);
        result.gurobi_seed_get_return_code =
            api.getintparam(env, GRB_INT_PAR_SEED,
                            &result.gurobi_seed_effective);
        result.gurobi_mip_gap_get_return_code =
            api.getdblparam(env, GRB_DBL_PAR_MIPGAP,
                            &result.gurobi_mip_gap_effective);
        result.gurobi_mip_gap_abs_get_return_code =
            api.getdblparam(env, GRB_DBL_PAR_MIPGAPABS,
                            &result.gurobi_mip_gap_abs_effective);

        int rc = api.readmodel(env, lp_path.string().c_str(), &model);
        if (rc != 0 || !model) {
            result.status = "model_read_failed";
            result.gurobi_failure_reason = apiError(api, env, rc);
            result.strict_certificate_class = "certificate_rejected";
            result.strict_certificate_rejection_reason =
                result.gurobi_failure_reason;
            cleanup();
            result.runtime_seconds =
                std::chrono::duration<double>(Clock::now() - start).count();
            result.wall_time_seconds = result.runtime_seconds;
            return result;
        }
        ++result.gurobi_model_count;
        ++result.gurobi_model_read_count;
        GRBenv* model_env = api.getenv(model);
        // Readbacks from the model environment are authoritative for the
        // optimize call.
        if (model_env) {
            result.gurobi_threads_get_return_code =
                api.getintparam(model_env, GRB_INT_PAR_THREADS,
                                &result.gurobi_threads_effective);
            result.gurobi_presolve_get_return_code =
                api.getintparam(model_env, GRB_INT_PAR_PRESOLVE,
                                &result.gurobi_presolve_effective);
            result.gurobi_seed_get_return_code =
                api.getintparam(model_env, GRB_INT_PAR_SEED,
                                &result.gurobi_seed_effective);
            result.gurobi_mip_gap_get_return_code =
                api.getdblparam(model_env, GRB_DBL_PAR_MIPGAP,
                                &result.gurobi_mip_gap_effective);
            result.gurobi_mip_gap_abs_get_return_code =
                api.getdblparam(model_env, GRB_DBL_PAR_MIPGAPABS,
                                &result.gurobi_mip_gap_abs_effective);
        }

        auto getInt = [&](const char* attr, int& target) {
            return api.getintattr(model, attr, &target) == 0;
        };
        auto getDouble = [&](const char* attr, double& target) {
            return api.getdblattr(model, attr, &target) == 0 &&
                std::isfinite(target);
        };
        getInt(GRB_INT_ATTR_NUMVARS, result.gurobi_num_vars);
        getInt(GRB_INT_ATTR_NUMCONSTRS, result.gurobi_num_constrs);
        getDouble(GRB_DBL_ATTR_DNUMNZS, result.gurobi_num_nzs);
        getInt(GRB_INT_ATTR_NUMBINVARS, result.gurobi_num_bin_vars);
        getInt(GRB_INT_ATTR_NUMINTVARS, result.gurobi_num_int_vars);
        getInt(GRB_INT_ATTR_MODELSENSE, result.gurobi_objective_sense);
        getInt(GRB_INT_ATTR_FINGERPRINT, result.gurobi_model_fingerprint);

        const CanonicalLpVariableAudit expected_domain =
            parseCanonicalLpVariableAudit(lp_path);
        std::vector<double> native_lb(
            static_cast<std::size_t>(std::max(0, result.gurobi_num_vars)));
        std::vector<double> native_ub(native_lb.size());
        std::vector<char> native_type(native_lb.size());
        std::unordered_map<std::string, CanonicalLpVariableAudit::Variable>
            native_domain;
        bool native_arrays_ok = result.gurobi_num_vars >= 0 &&
            api.getdblattrarray(model, GRB_DBL_ATTR_LB, 0,
                result.gurobi_num_vars, native_lb.data()) == 0 &&
            api.getdblattrarray(model, GRB_DBL_ATTR_UB, 0,
                result.gurobi_num_vars, native_ub.data()) == 0 &&
            api.getcharattrarray(model, GRB_CHAR_ATTR_VTYPE, 0,
                result.gurobi_num_vars, native_type.data()) == 0;
        result.gurobi_num_bin_vars = 0;
        result.gurobi_num_int_vars = 0;
        result.gurobi_num_cont_vars = 0;
        for (int index = 0; native_arrays_ok &&
             index < result.gurobi_num_vars; ++index) {
            char* name = nullptr;
            native_arrays_ok = api.getstrattrelement(
                model, GRB_STR_ATTR_VARNAME, index, &name) == 0 &&
                name && *name;
            if (!native_arrays_ok) break;
            native_domain[name] = {
                native_lb[static_cast<std::size_t>(index)],
                native_ub[static_cast<std::size_t>(index)],
                native_type[static_cast<std::size_t>(index)]};
            if (native_type[static_cast<std::size_t>(index)] == GRB_BINARY) {
                ++result.gurobi_num_bin_vars;
            } else if (native_type[static_cast<std::size_t>(index)] ==
                       GRB_INTEGER) {
                ++result.gurobi_num_int_vars;
            } else {
                ++result.gurobi_num_cont_vars;
            }
        }
        result.gurobi_native_variable_names_match = expected_domain.parsed &&
            native_arrays_ok &&
            native_domain.size() == expected_domain.variables.size();
        result.gurobi_native_variable_types_match =
            result.gurobi_native_variable_names_match;
        result.gurobi_native_variable_bounds_match =
            result.gurobi_native_variable_names_match;
        if (result.gurobi_native_variable_names_match) {
            for (const auto& expected : expected_domain.variables) {
                const auto native = native_domain.find(expected.first);
                if (native == native_domain.end()) {
                    result.gurobi_native_variable_names_match = false;
                    result.gurobi_native_variable_types_match = false;
                    result.gurobi_native_variable_bounds_match = false;
                    break;
                }
                result.gurobi_native_variable_types_match =
                    result.gurobi_native_variable_types_match &&
                    native->second.type == expected.second.type;
                const double scale = std::max({1.0,
                    std::fabs(expected.second.lower),
                    std::fabs(expected.second.upper)});
                result.gurobi_native_variable_bounds_match =
                    result.gurobi_native_variable_bounds_match &&
                    std::fabs(native->second.lower - expected.second.lower) <=
                        1e-12 * scale &&
                    std::fabs(native->second.upper - expected.second.upper) <=
                        1e-12 * scale;
            }
        }
        result.gurobi_native_objective_sense_match = expected_domain.parsed &&
            result.gurobi_objective_sense == expected_domain.objective_sense;
        result.gurobi_native_domain_audit_passed = expected_domain.parsed &&
            native_arrays_ok && result.gurobi_native_variable_names_match &&
            result.gurobi_native_variable_types_match &&
            result.gurobi_native_variable_bounds_match &&
            result.gurobi_native_objective_sense_match;
        if (result.gurobi_native_domain_audit_passed) {
            result.gurobi_native_domain_audit_failure_reason = "none";
        } else {
            std::ostringstream audit;
            audit << "parse=" << expected_domain.parsed
                  << ";native_arrays=" << native_arrays_ok
                  << ";names=" << result.gurobi_native_variable_names_match
                  << ";types=" << result.gurobi_native_variable_types_match
                  << ";bounds=" << result.gurobi_native_variable_bounds_match
                  << ";objective_sense="
                  << result.gurobi_native_objective_sense_match
                  << ";parse_reason=" << expected_domain.failure_reason;
            result.gurobi_native_domain_audit_failure_reason = audit.str();
        }

        ProgressCallbackState callback;
        callback.api = &api;
        const int callback_rc = api.setcallbackfunc(
            model, readOnlyProgressCallback, &callback);
        if (callback_rc != 0) {
            result.status = "callback_configuration_failed";
            result.gurobi_failure_reason = apiError(api, env, callback_rc);
            result.strict_certificate_class = "certificate_rejected";
            result.strict_certificate_rejection_reason =
                result.gurobi_failure_reason;
            cleanup();
            result.runtime_seconds =
                std::chrono::duration<double>(Clock::now() - start).count();
            result.wall_time_seconds = result.runtime_seconds;
            return result;
        }

        // Model export, environment startup, model import, and domain audits
        // are inside the same process-entry work window. Recompute the native
        // allowance at Optimize launch instead of rebasing a solver-only
        // duration before those phases.
        const double optimize_remaining =
            processDeadlineConfigured(options)
                ? processWorkRemainingSeconds(options)
                : options.solve_time_limit;
        time_limit_rc = time_limit_rc == 0
            ? api.setdblparam(
                  model_env, GRB_DBL_PAR_TIMELIMIT,
                  std::max(0.001, optimize_remaining))
            : time_limit_rc;
        recordProcessPhase(
            options, "plain_gurobi_optimize_launch", "start",
            "absolute_work_remaining=" +
                std::to_string(optimize_remaining));
        result.gurobi_optimize_return_code = api.optimize(model);
        ++result.gurobi_optimize_count;
        result.gurobi_solver_finalization_reached = true;
        getInt(GRB_INT_ATTR_STATUS, result.gurobi_status);
        result.gurobi_status_text = gurobiStatusName(result.gurobi_status);
        getInt(GRB_INT_ATTR_SOLCOUNT, result.gurobi_solution_count);
        result.gurobi_obj_bound_available =
            getDouble(GRB_DBL_ATTR_OBJBOUND, result.gurobi_obj_bound);
        result.gurobi_obj_bound_c_available =
            getDouble(GRB_DBL_ATTR_OBJBOUNDC, result.gurobi_obj_bound_c);
        if (result.gurobi_solution_count > 0) {
            result.gurobi_obj_val_available =
                getDouble(GRB_DBL_ATTR_OBJVAL, result.gurobi_obj_val);
            result.gurobi_mip_gap_available =
                getDouble(GRB_DBL_ATTR_MIPGAP, result.gurobi_mip_gap);
        }
        getDouble(GRB_DBL_ATTR_RUNTIME, result.gurobi_runtime);
        getDouble(GRB_DBL_ATTR_WORK, result.gurobi_work);
        getDouble(GRB_DBL_ATTR_NODECOUNT, result.gurobi_node_count);
        getDouble(GRB_DBL_ATTR_ITERCOUNT, result.gurobi_iter_count);
        getInt(GRB_INT_ATTR_BARITERCOUNT, result.gurobi_bar_iter_count);
        getDouble(GRB_DBL_ATTR_MEMUSED, result.gurobi_mem_used_gb);
        getDouble(GRB_DBL_ATTR_MAXMEMUSED, result.gurobi_max_mem_used_gb);
        if (result.gurobi_solution_count > 0) {
            getDouble(GRB_DBL_ATTR_CONSTR_VIO,
                      result.gurobi_max_constraint_violation);
            getDouble(GRB_DBL_ATTR_BOUND_VIO,
                      result.gurobi_max_bound_violation);
            getDouble(GRB_DBL_ATTR_INT_VIO,
                      result.gurobi_max_integrality_violation);
        }

        std::unordered_map<std::string, double> values;
        bool verified_original_feasible = false;
        bool objective_recomputed = false;
        if (result.gurobi_solution_count > 0 && result.gurobi_num_vars > 0) {
            std::vector<double> x(
                static_cast<std::size_t>(result.gurobi_num_vars), 0.0);
            if (api.getdblattrarray(model, GRB_DBL_ATTR_X, 0,
                                    result.gurobi_num_vars, x.data()) == 0) {
                for (int index = 0; index < result.gurobi_num_vars; ++index) {
                    char* name = nullptr;
                    if (api.getstrattrelement(
                            model, GRB_STR_ATTR_VARNAME, index, &name) == 0 &&
                        name && *name) {
                        values[name] = x[static_cast<std::size_t>(index)];
                    }
                }
            }
            result.routes =
                reconstructCanonicalCompactRoutes(instance, values);
            result.verification =
                verifySolution(instance, result.routes, options.lambda);
            verified_original_feasible =
                result.verification.original_solution_feasible &&
                result.verification.errors.empty();
            objective_recomputed =
                result.verification.original_objective_recomputed &&
                std::isfinite(result.verification.objective);
            if (verified_original_feasible && objective_recomputed) {
                result.final_inventory = result.verification.final_inventory;
                result.G = result.verification.G;
                result.P = result.verification.P;
                result.objective = result.verification.objective;
                result.upper_bound = result.verification.objective;
                result.verified_incumbent_objective_available = true;
                result.verified_incumbent_objective = result.objective;
                result.verified_incumbent_original_problem_feasible = true;
                result.verified_incumbent_objective_consistent =
                    result.gurobi_obj_val_available &&
                    std::fabs(result.objective - result.gurobi_obj_val) <=
                        1e-8 * std::max({1.0, std::fabs(result.objective),
                                         std::fabs(result.gurobi_obj_val)});
                result.verified_incumbent_objective_residual_available =
                    result.gurobi_obj_val_available;
                if (result.gurobi_obj_val_available) {
                    result.verified_incumbent_objective_residual =
                        result.gurobi_obj_val - result.objective;
                }
            }
        }
        if (result.gurobi_obj_bound_c_available) {
            result.lower_bound = result.gurobi_obj_bound_c;
        }
        if (result.upper_bound > 0.0 &&
            result.gurobi_obj_bound_c_available) {
            result.gap = std::max(
                0.0, (result.upper_bound - result.lower_bound) /
                         std::fabs(result.upper_bound));
        }

        if (callback.progress.events.empty() ||
            callback.progress.events.back().elapsed_runtime_seconds + 1e-12 <
                result.gurobi_runtime) {
            GurobiProgressEvent final_event;
            final_event.elapsed_runtime_seconds = result.gurobi_runtime;
            final_event.work = result.gurobi_work;
            final_event.incumbent_available = result.gurobi_obj_val_available;
            final_event.incumbent = result.gurobi_obj_val;
            final_event.best_bound_available =
                result.gurobi_obj_bound_c_available;
            final_event.best_bound = result.gurobi_obj_bound_c;
            final_event.processed_nodes = result.gurobi_node_count;
            final_event.solution_count = result.gurobi_solution_count;
            final_event.callback_where = -1;
            final_event.context = "solver_final";
            callback.progress.events.push_back(final_event);
            ++callback.progress.records;
        }
        std::string progress_reason;
        writeGurobiProgressCsv(
            progress_path, callback.progress, &progress_reason);
        result.gurobi_progress_callback_invocations =
            callback.progress.callback_invocations;
        result.gurobi_progress_record_count = callback.progress.records;
        result.gurobi_first_incumbent_time =
            callback.progress.first_incumbent_time;
        result.gurobi_last_lower_bound_improvement_time =
            callback.progress.last_lower_bound_improvement_time;
        result.gurobi_progress_read_only_contract =
            callback.progress.read_only_contract &&
            !callback.progress.deadline_termination_used;

        result.native_mip_evidence_available =
            result.gurobi_optimize_return_code == 0;
        result.native_mipopt_return_code = result.gurobi_optimize_return_code;
        result.native_mip_status_code = result.gurobi_status;
        result.native_mip_status_text_available = true;
        result.native_mip_status_text = result.gurobi_status_text;
        result.native_mip_status_class =
            gurobiStatusClass(result.gurobi_status);
        result.native_mip_status_code_text_consistent = true;
        result.native_mip_objective_available =
            result.gurobi_obj_val_available;
        result.native_mip_objective = result.gurobi_obj_val;
        result.native_mip_best_bound_available =
            result.gurobi_obj_bound_c_available;
        result.native_mip_best_bound = result.gurobi_obj_bound_c;
        result.native_mip_solution_count_available = true;
        result.native_mip_solution_count = result.gurobi_solution_count;
        result.native_mip_node_count_available = true;
        result.native_mip_node_count = static_cast<long long>(
            std::llround(result.gurobi_node_count));
        result.native_mip_relative_gap_param_id = -1;
        result.native_mip_relative_gap_requested = 0.0;
        result.native_mip_relative_gap_set_return_code =
            result.gurobi_mip_gap_set_return_code;
        result.native_mip_relative_gap_get_return_code =
            result.gurobi_mip_gap_get_return_code;
        result.native_mip_relative_gap_effective_available =
            result.gurobi_mip_gap_get_return_code == 0;
        result.native_mip_relative_gap_effective =
            result.gurobi_mip_gap_effective;
        result.native_mip_absolute_gap_param_id = -1;
        result.native_mip_absolute_gap_requested = 0.0;
        result.native_mip_absolute_gap_set_return_code =
            result.gurobi_mip_gap_abs_set_return_code;
        result.native_mip_absolute_gap_get_return_code =
            result.gurobi_mip_gap_abs_get_return_code;
        result.native_mip_absolute_gap_effective_available =
            result.gurobi_mip_gap_abs_get_return_code == 0;
        result.native_mip_absolute_gap_effective =
            result.gurobi_mip_gap_abs_effective;
        result.native_mip_strict_gap_parameters_valid =
            result.gurobi_mip_gap_set_return_code == 0 &&
            result.gurobi_mip_gap_get_return_code == 0 &&
            result.gurobi_mip_gap_effective == 0.0 &&
            result.gurobi_mip_gap_abs_set_return_code == 0 &&
            result.gurobi_mip_gap_abs_get_return_code == 0 &&
            result.gurobi_mip_gap_abs_effective == 0.0;
        result.native_mip_environment_count = result.gurobi_environment_count;
        result.native_mip_problem_count = result.gurobi_model_count;
        result.native_mip_model_read_count = result.gurobi_model_read_count;
        result.native_mip_mipopt_count = result.gurobi_optimize_count;
        result.native_mip_solver_finalization_reached = true;
        result.native_mip_evidence_capture_complete = true;

        cleanup();
        result.native_mip_problem_freed = model_free_rc == 0;
        result.native_mip_environment_closed =
            result.gurobi_environment_free_count == 1;
        result.native_mip_freeprob_return_code = model_free_rc;
        result.native_mip_close_return_code = 0;
        result.native_mip_freeprob_count = result.gurobi_model_free_count;
        result.native_mip_close_count =
            result.gurobi_environment_free_count;
        result.gurobi_lifecycle_valid =
            result.gurobi_environment_count == 1 &&
            result.gurobi_model_count == 1 &&
            result.gurobi_model_read_count == 1 &&
            result.gurobi_optimize_count == 1 &&
            result.gurobi_model_free_count == 1 &&
            result.gurobi_environment_free_count == 1 && model_free_rc == 0;
        result.native_mip_lifecycle_valid = result.gurobi_lifecycle_valid;

        const bool configuration_valid =
            result.gurobi_threads_set_return_code == 0 &&
            result.gurobi_threads_get_return_code == 0 &&
            result.gurobi_threads_effective == 1 &&
            result.gurobi_presolve_set_return_code == 0 &&
            result.gurobi_presolve_get_return_code == 0 &&
            result.gurobi_presolve_effective == options.gurobi_presolve &&
            result.gurobi_seed_set_return_code == 0 &&
            result.gurobi_seed_get_return_code == 0 &&
            result.gurobi_seed_effective == options.gurobi_seed &&
            result.native_mip_strict_gap_parameters_valid &&
            time_limit_rc == 0;
        const bool no_external_information =
            options.incumbent_json_path.empty() &&
            options.hga_incumbent_path.empty() &&
            options.external_incumbent_path.empty() &&
            !options.gcap_seed_cplex;
        GurobiCertificateInput certificate_input;
        certificate_input.status = result.gurobi_status;
        certificate_input.optimize_returned =
            result.gurobi_optimize_return_code == 0;
        certificate_input.solver_finalization_completed =
            result.gurobi_solver_finalization_reached;
        certificate_input.complete_original_model_scope =
            result.gurobi_native_domain_audit_passed;
        certificate_input.model_configuration_valid = configuration_valid;
        certificate_input.lifecycle_valid = result.gurobi_lifecycle_valid;
        certificate_input.executable_fingerprint_matches_manifest =
            !options.round24_executable_sha256.empty() &&
            options.round24_executable_sha256 ==
                options.round24_manifest_executable_sha256;
        certificate_input.model_fingerprint_matches_manifest =
            options.round24_expected_gurobi_model_fingerprint != 0 &&
            result.gurobi_model_fingerprint ==
                options.round24_expected_gurobi_model_fingerprint;
        certificate_input.no_tailored_or_external_information =
            no_external_information;
        certificate_input.relative_gap_requested_exact_zero = true;
        certificate_input.relative_gap_readback_exact_zero =
            result.gurobi_mip_gap_get_return_code == 0 &&
            result.gurobi_mip_gap_effective == 0.0;
        certificate_input.absolute_gap_requested_exact_zero = true;
        certificate_input.absolute_gap_readback_exact_zero =
            result.gurobi_mip_gap_abs_get_return_code == 0 &&
            result.gurobi_mip_gap_abs_effective == 0.0;
        certificate_input.finite_solution_available =
            result.gurobi_obj_val_available;
        certificate_input.independently_verified_original_feasible =
            verified_original_feasible;
        certificate_input.objective_recomputed = objective_recomputed;
        certificate_input.verified_feasible_witness_available =
            verified_original_feasible;
        const GurobiCertificateDecision decision =
            evaluateGurobiEngineeringExactCertificate(certificate_input);
        result.strict_certificate_policy_version = decision.policy_version;
        result.strict_certificate_class = decision.certificate_class;
        result.strict_certificate_rejection_reason = decision.rejection_reason;
        result.strict_native_model_scope = decision.native_model_scope;
        result.strict_infeasibility_scope = decision.infeasibility_scope;
        result.feasibility_consistency_gate_passed =
            decision.feasibility_consistency_gate_passed;
        result.strict_certified_original_problem =
            decision.strict_certified_original_problem;
        result.strict_lower_bound_source = result.gurobi_obj_bound_c_available
            ? "Gurobi_ObjBoundC" : "unavailable";

        if (decision.strict_certified_original_problem) {
            result.status = "optimal";
            result.certificate =
                "Round 24 Gurobi engineering-exact certificate: OPTIMAL on "
                "the audited complete original compact model, exact-zero "
                "MIPGap and MIPGapAbs round trips, completed lifecycle, "
                "frozen model/executable bindings, and independent original-"
                "problem verification.";
        } else if (decision.original_problem_infeasible_certified) {
            result.status = "infeasible";
            result.certificate =
                "Round 24 Gurobi engineering-exact original-problem "
                "infeasibility certificate.";
        } else if (result.gurobi_status == kGurobiStatusTimeLimit) {
            result.status = "time_limit";
            result.certificate =
                "not_certified; valid native continuous bound retained from "
                "ObjBoundC when available";
        } else if (result.gurobi_optimize_return_code != 0) {
            result.status = "error";
            result.certificate = "not_certified";
        } else {
            result.status = "not_certified";
            result.certificate = "Strict Gurobi certificate rejected: " +
                decision.rejection_reason;
        }
#else
        result.status = "backend_unavailable";
        result.gurobi_failure_reason =
            "gurobi_dynamic_backend_requires_windows";
        result.strict_certificate_class = "certificate_rejected";
        result.strict_certificate_rejection_reason =
            result.gurobi_failure_reason;
#endif
    } catch (const std::exception& ex) {
        result.status = "error";
        result.gurobi_exception_type = "std::exception";
        result.gurobi_exception_message = ex.what();
        result.gurobi_failure_reason = ex.what();
        result.strict_certificate_class = "certificate_rejected";
        result.strict_certificate_rejection_reason =
            "gurobi_exception:" + std::string(ex.what());
        result.certificate = "not_certified";
    }
    result.runtime_seconds =
        std::chrono::duration<double>(Clock::now() - start).count();
    result.wall_time_seconds = result.runtime_seconds;
    result.actual_runtime_seconds = result.runtime_seconds;
    return result;
}

std::unique_ptr<FixedIntervalMipBackend> makeGurobiFixedIntervalBackend(
    const Instance& instance, const SolveOptions& options) {
#ifdef _WIN32
    return std::make_unique<GurobiFixedIntervalBackend>(instance, options);
#else
    (void)instance;
    (void)options;
    return {};
#endif
}

} // namespace ebrp
