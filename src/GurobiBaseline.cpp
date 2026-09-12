#include "GurobiBaseline.hpp"

#include "CanonicalCompactModel.hpp"
#include "ControllingLeafScheduler.hpp"
#include "Evaluator.hpp"
#include "FileSha256.hpp"
#include "FixedIntervalMipBackend.hpp"
#include "GurobiCertificate.hpp"
#include "GurobiProgress.hpp"
#include "HgaTgbcRunner.hpp"
#include "ProcessPhaseLedger.hpp"
#include "MipStartMapping.hpp"
#include "Round50IntervalMip.hpp"
#include "Round53CallbackIsolation.hpp"
#include "Round52GurobiCutAdapter.hpp"
#include "Round52TailoredCuts.hpp"
#include "Round60Candidates.hpp"
#include "Round61Candidates.hpp"

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
#include <regex>
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
    decltype(&GRBcbsolution) cbsolution = nullptr;
    decltype(&GRBcbcut) cbcut = nullptr;
    decltype(&GRBcblazy) cblazy = nullptr;
    decltype(&GRBterminate) terminate = nullptr;
    decltype(&GRBoptimize) optimize = nullptr;
    decltype(&GRBgetintattr) getintattr = nullptr;
    decltype(&GRBgetdblattr) getdblattr = nullptr;
    decltype(&GRBgetintattrarray) getintattrarray = nullptr;
    decltype(&GRBgetstrattrelement) getstrattrelement = nullptr;
    decltype(&GRBgetdblattrarray) getdblattrarray = nullptr;
    decltype(&GRBgetcharattrarray) getcharattrarray = nullptr;
    decltype(&GRBsetdblattrarray) setdblattrarray = nullptr;
    decltype(&GRBsetintattrarray) setintattrarray = nullptr;
    decltype(&GRBsetcharattrarray) setcharattrarray = nullptr;
    decltype(&GRBaddconstr) addconstr = nullptr;
    decltype(&GRBupdatemodel) updatemodel = nullptr;
    decltype(&GRBwrite) write = nullptr;
    decltype(&GRBgetconstrs) getconstrs = nullptr;
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
    LOAD_GRB(cbsolution, "GRBcbsolution");
    LOAD_GRB(cbcut, "GRBcbcut");
    LOAD_GRB(cblazy, "GRBcblazy");
    LOAD_GRB(terminate, "GRBterminate");
    LOAD_GRB(optimize, "GRBoptimize");
    LOAD_GRB(getintattr, "GRBgetintattr");
    LOAD_GRB(getdblattr, "GRBgetdblattr");
    LOAD_GRB(getintattrarray, "GRBgetintattrarray");
    LOAD_GRB(getstrattrelement, "GRBgetstrattrelement");
    LOAD_GRB(getdblattrarray, "GRBgetdblattrarray");
    LOAD_GRB(getcharattrarray, "GRBgetcharattrarray");
    LOAD_GRB(setdblattrarray, "GRBsetdblattrarray");
    LOAD_GRB(setintattrarray, "GRBsetintattrarray");
    LOAD_GRB(setcharattrarray, "GRBsetcharattrarray");
    LOAD_GRB(addconstr, "GRBaddconstr");
    LOAD_GRB(updatemodel, "GRBupdatemodel");
    LOAD_GRB(write, "GRBwrite");
    LOAD_GRB(getconstrs, "GRBgetconstrs");
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
    struct RootScalar {
        long long callback_sequence = 0;
        double node_count = 0.0;
        double relaxation_objective = 0.0;
        double incumbent = 0.0;
        bool incumbent_available = false;
    };
    std::ostream* round59_samples = nullptr;
    std::vector<std::string> round59_names;
    std::set<int> round59_sampled;
    long long round59_root_callback_sequence = 0;
    std::vector<double> round59_first_root_values;
    std::vector<double> round59_latest_root_values;
    std::vector<std::pair<int, std::vector<double>>> round59_nonroot_values;
    std::vector<RootScalar> round59_root_scalars;
    bool round59_nonroot_observed = false;
    double round59_sample_seconds = 0.0;
    long long round59_sample_checks = 0;
    int round59_sample_successes = 0;
    GurobiApi* api = nullptr;
    GurobiProgressStats progress;
    Clock::time_point telemetry_start = Clock::now();
    double last_record_time = -1.0;
    double last_incumbent = std::numeric_limits<double>::infinity();
    double last_bound = -std::numeric_limits<double>::infinity();
    bool bound_target_enabled = false;
    double bound_target = 0.0;
    double bound_target_tolerance = 1e-7;
    bool bound_target_reached = false;
    bool bound_target_termination_requested = false;
    bool round53_mipnode_path_active = false;
    bool round53_relaxation_vector_active = false;
    bool round53_separator_active = false;
    bool round53_cut_submission_active = false;
    bool tailored_cut_active = false;
    bool tailored_cut_disabled_after_failure = false;
    const Instance* cut_instance = nullptr;
    Round52SupportDurationSeparator* cut_separator = nullptr;
    Round52CutManager* cut_manager = nullptr;
    Round52CutSeparationScope cut_scope =
        Round52CutSeparationScope::RootOnly;
    int cut_support_rank = 3;
    double cut_certificate_tolerance = 1e-7;
    std::string cut_interval_id;
    std::unordered_map<std::string, int> cut_variable_indices;
    std::vector<std::string> cut_variable_names;
    std::vector<double> cut_lower_bounds;
    std::vector<double> cut_upper_bounds;
    std::vector<double> cut_relaxation_values;
    long long cut_nonoptimal_mipnode_callbacks = 0;
    long long cut_relaxation_vector_failures = 0;
    long long cut_adapter_failures = 0;
    long long round53_mipnode_calls = 0;
    long long round53_mipnode_status_reads = 0;
    long long round53_relaxation_vector_reads = 0;
    long long round53_separator_calls = 0;
    long long round53_cut_submission_calls = 0;
    double cut_callback_overhead_seconds = 0.0;

    const Instance* candidate_instance = nullptr;
    const SolveOptions* candidate_options = nullptr;
    std::string candidate_mode = "off";
    std::shared_ptr<Round61CandidateSession> round61_session;
    std::function<bool(double)> round62_external_stop;
    bool round62_external_termination_requested = false;
    std::string candidate_model_identity;
    double candidate_gamma_L = 0.0;
    double candidate_gamma_U = 0.0;
    double candidate_cutoff = 0.0;
    int candidate_maximum_evaluations = 512;
    int candidate_maximum_stations = 16;
    SolverNeutralModelDomain candidate_domain;
    SolverNeutralLinearModel candidate_linear_model;
    bool candidate_data_triggered = false;
    int candidate_root_triggers = 0;
    bool candidate_disabled_after_failure = false;
    long long candidate_trigger_count = 0;
    double candidate_overhead_seconds = 0.0;
    std::vector<FixedIntervalCandidateEvent> candidate_events;
    std::set<std::string> candidate_hashes;
    double candidate_best_verified_objective =
        std::numeric_limits<double>::infinity();
    struct SubmittedCandidate {
        std::size_t event_index = 0;
        std::vector<double> values;
        double objective = 0.0;
        bool confirmed = false;
    };
    std::vector<SubmittedCandidate> submitted_candidates;
};

bool finiteNative(double value) {
    return std::isfinite(value) && std::fabs(value) < GRB_INFINITY;
}

bool readLinearModel(const GurobiApi& api,
                     GRBmodel* model,
                     int variables,
                     int rows,
                     SolverNeutralLinearModel& out) {
    out = SolverNeutralLinearModel{};
    if (!model || variables < 0 || rows < 0 || !api.getconstrs) return false;
    double native_nonzeros = 0.0;
    if (api.getdblattr(model, GRB_DBL_ATTR_DNUMNZS, &native_nonzeros) != 0 ||
        !std::isfinite(native_nonzeros) || native_nonzeros < 0.0 ||
        native_nonzeros > static_cast<double>(std::numeric_limits<int>::max())) {
        return false;
    }
    const int expected_nonzeros = static_cast<int>(std::llround(native_nonzeros));
    std::vector<int> starts(static_cast<std::size_t>(rows));
    std::vector<int> indices(static_cast<std::size_t>(expected_nonzeros));
    std::vector<double> coefficients(
        static_cast<std::size_t>(expected_nonzeros));
    int actual_nonzeros = 0;
    if (rows > 0 && api.getconstrs(
            model, &actual_nonzeros, starts.data(), indices.data(),
            coefficients.data(), 0, rows) != 0) {
        return false;
    }
    if (actual_nonzeros < 0 || actual_nonzeros > expected_nonzeros) return false;
    indices.resize(static_cast<std::size_t>(actual_nonzeros));
    coefficients.resize(static_cast<std::size_t>(actual_nonzeros));
    out.variable_count = variables;
    out.row_starts = std::move(starts);
    out.row_starts.push_back(actual_nonzeros);
    out.column_indices = std::move(indices);
    out.coefficients = std::move(coefficients);
    out.senses.resize(static_cast<std::size_t>(rows));
    out.rhs.resize(static_cast<std::size_t>(rows));
    return rows == 0 ||
        (api.getcharattrarray(model, GRB_CHAR_ATTR_SENSE, 0, rows,
                             out.senses.data()) == 0 &&
         api.getdblattrarray(model, GRB_DBL_ATTR_RHS, 0, rows,
                            out.rhs.data()) == 0);
}

bool parseSingleIndex(const std::string& name,
                      const std::string& prefix,
                      int& index) {
    if (name.rfind(prefix, 0) != 0 || name.size() == prefix.size()) {
        return false;
    }
    const std::string token = name.substr(prefix.size());
    if (!std::all_of(token.begin(), token.end(), [](unsigned char ch) {
            return ch >= '0' && ch <= '9';
        })) {
        return false;
    }
    index = std::stoi(token);
    return true;
}

bool parseTwoIndices(const std::string& name,
                     const std::string& prefix,
                     int& first,
                     int& second) {
    if (name.rfind(prefix, 0) != 0) return false;
    const std::string rest = name.substr(prefix.size());
    const std::size_t separator = rest.find('_');
    if (separator == std::string::npos || separator == 0 ||
        separator + 1 >= rest.size()) {
        return false;
    }
    const std::string a = rest.substr(0, separator);
    const std::string b = rest.substr(separator + 1);
    const auto digits = [](const std::string& value) {
        return !value.empty() && std::all_of(
            value.begin(), value.end(), [](unsigned char ch) {
                return ch >= '0' && ch <= '9';
            });
    };
    if (!digits(a) || !digits(b)) return false;
    first = std::stoi(a);
    second = std::stoi(b);
    return true;
}

void attemptRound60Candidate(
    ProgressCallbackState& state,
    void* cbdata,
    int where,
    const std::string& trigger,
    const std::vector<double>* relaxation) {
    if (!state.candidate_instance || !state.candidate_options ||
        state.candidate_mode == "off" ||
        state.candidate_disabled_after_failure) {
        return;
    }
    const auto started = Clock::now();
    FixedIntervalCandidateEvent event;
    event.event_sequence = ++state.candidate_trigger_count;
    event.callback_where = where;
    event.trigger = trigger;
    event.mode = state.candidate_mode;
    event.callback_elapsed_seconds = std::chrono::duration<double>(
        started - state.telemetry_start).count();

    Round60ConstructionInput construction;
    construction.source = relaxation
        ? "round60_root_relaxation_guided_repair"
        : "round60_early_data_target_greedy";
    construction.model_identity = state.candidate_model_identity;
    construction.maximum_evaluations = state.candidate_maximum_evaluations;
    construction.maximum_stations = state.candidate_maximum_stations;
    construction.desired_inventory = state.candidate_instance->target;
    if (relaxation && relaxation->size() ==
            state.candidate_domain.names.size()) {
        for (std::size_t column = 0; column < relaxation->size(); ++column) {
            const std::string& name = state.candidate_domain.names[column];
            const double value = (*relaxation)[column];
            int station = 0;
            if (parseSingleIndex(name, "Y_", station) && station >= 1 &&
                station <= state.candidate_instance->V &&
                std::isfinite(value)) {
                construction.desired_inventory[station] =
                    static_cast<int>(std::llround(value));
            }
            if ((name.rfind("x_", 0) == 0 ||
                 name.rfind("z_", 0) == 0) && std::isfinite(value)) {
                construction.relaxation_values.emplace(name, value);
            }
        }
    }

    Round60ConstructionResult built;
    if(state.round61_session) {
        construction.source = "PREFIX_precomputed_once";
        built.candidate = state.round61_session->archive;
        built.generated = built.candidate.verified;
        built.generation_seconds = state.round61_session->construction_seconds;
        built.reason = "precomputed_verified_archive";
        event.mode = state.round61_session->mode;
    } else built = constructRound60BrpCandidate(
        *state.candidate_instance, state.candidate_options->lambda, construction);
    event.source = construction.source;
    event.generated = built.generated;
    event.objective_evaluations = built.objective_evaluations;
    event.generation_seconds = built.generation_seconds;
    event.status = built.reason;
    if (!built.generated) {
        event.total_seconds = std::chrono::duration<double>(
            Clock::now() - started).count();
        state.candidate_overhead_seconds += event.total_seconds;
        state.candidate_events.push_back(std::move(event));
        return;
    }

    event.independently_verified = built.candidate.verified;
    event.verification_seconds = built.candidate.verification_seconds;
    event.candidate_objective = built.candidate.objective;
    event.content_sha256 = built.candidate.content_sha256;
    if (!state.candidate_hashes.insert(event.content_sha256).second) {
        event.status = "duplicate_candidate_hash_not_resubmitted";
        event.total_seconds = std::chrono::duration<double>(
            Clock::now() - started).count();
        state.candidate_overhead_seconds += event.total_seconds;
        state.candidate_events.push_back(std::move(event));
        return;
    }
    const double cutoff_tolerance = 1e-8 * std::max(
        {1.0, std::fabs(state.candidate_cutoff),
         std::fabs(event.candidate_objective)});
    event.strictly_improves_frozen_cutoff =
        event.candidate_objective < state.candidate_cutoff - cutoff_tolerance;
    const double published_tolerance = 1e-8 * std::max(
        {1.0, std::fabs(event.candidate_objective),
         std::isfinite(state.candidate_best_verified_objective)
             ? std::fabs(state.candidate_best_verified_objective) : 1.0});
    const bool improves_published_candidate =
        !std::isfinite(state.candidate_best_verified_objective) ||
        event.candidate_objective <
            state.candidate_best_verified_objective - published_tolerance;
    double native_incumbent = GRB_INFINITY;
    if(state.round61_session) state.api->cbget(cbdata,where,
        where==GRB_CB_MIP ? GRB_CB_MIP_OBJBST : GRB_CB_MIPNODE_OBJBST,&native_incumbent);
    event.native_incumbent_before_available = finiteNative(native_incumbent);
    if(event.native_incumbent_before_available) event.native_incumbent_before_submission = native_incumbent;
    const bool cutoff_admissible = state.round61_session
        ? event.candidate_objective <= state.candidate_cutoff + cutoff_tolerance
        : event.strictly_improves_frozen_cutoff;
    const bool admitted = state.round61_session
        ? round61ShouldSubmitCandidate(event.candidate_objective,
            state.candidate_cutoff,event.native_incumbent_before_available,native_incumbent)
        : event.strictly_improves_frozen_cutoff && improves_published_candidate;
    if (!admitted) {
        event.status = !cutoff_admissible
            ? (state.round61_session ? "verified_exceeds_current_model_cutoff"
                                     : "verified_but_not_strictly_better_than_frozen_cutoff")
            : (state.round61_session ? "verified_archive_not_better_than_current_native_incumbent"
                                     : "verified_but_not_strictly_better_than_published_candidate");
        event.total_seconds = std::chrono::duration<double>(
            Clock::now() - started).count();
        state.candidate_overhead_seconds += event.total_seconds;
        state.candidate_events.push_back(std::move(event));
        return;
    }
    if(!state.round61_session) state.candidate_best_verified_objective = event.candidate_objective;
    const SolverNeutralMipStart mapped = mapVerifiedRoutesToCanonicalModel(
        *state.candidate_instance, *state.candidate_options,
        built.candidate.routes, construction.source,
        state.candidate_gamma_L, state.candidate_gamma_U,
        state.candidate_cutoff, state.candidate_domain);
    event.mapping_seconds = mapped.mapping_seconds;
    event.mapping_complete = mapped.complete;
    event.bounds_valid = mapped.bounds_valid;
    event.integrality_valid = mapped.integrality_valid;
    if (!mapped.complete) {
        event.status = "mapping_rejected:" + mapped.failure_reason;
        event.total_seconds = std::chrono::duration<double>(
            Clock::now() - started).count();
        state.candidate_overhead_seconds += event.total_seconds;
        state.candidate_events.push_back(std::move(event));
        return;
    }

    const auto residual_started = Clock::now();
    const CandidateLinearResidual residual =
        validateCandidateLinearResidual(
            state.candidate_linear_model, mapped.values, 1e-7);
    event.residual_check_seconds = std::chrono::duration<double>(
        Clock::now() - residual_started).count();
    event.linear_constraints_checked = residual.checked;
    event.linear_constraints_valid = residual.valid;
    event.linear_rows_checked = residual.checked_rows;
    event.violated_linear_rows = residual.violated_rows;
    event.maximum_linear_violation = residual.maximum_violation;
    if (!residual.valid) {
        event.status = "current_mip_residual_rejected:" +
            residual.failure_reason;
        event.total_seconds = std::chrono::duration<double>(
            Clock::now() - started).count();
        state.candidate_overhead_seconds += event.total_seconds;
        state.candidate_events.push_back(std::move(event));
        return;
    }

    if(state.round61_session) state.candidate_best_verified_objective = event.candidate_objective;
    event.status = state.candidate_mode == "dry"
        ? "verified_mapped_dry_run" : "verified_mapped_pending_submission";
    if (state.candidate_mode == "inject") {
        double native_objective = GRB_INFINITY;
        event.submission_return_code = state.api->cbsolution(
            cbdata, mapped.values.data(), &native_objective);
        event.submitted = event.submission_return_code == 0;
        event.native_objective_returned = finiteNative(native_objective);
        event.native_objective = event.native_objective_returned
            ? native_objective : 0.0;
        if (!event.submitted) {
            event.status = "GRBcbsolution_failed";
            event.acceptance = "submission_failed";
            state.candidate_disabled_after_failure = true;
        } else if (event.native_objective_returned) {
            event.status = "submitted_and_immediately_processed";
            event.acceptance = "confirmed_by_finite_GRBcbsolution_objective";
        } else {
            event.status = "submitted_for_delayed_processing";
            event.acceptance = "unknown_pending_exact_vector_observation";
        }
    }
    event.total_seconds = std::chrono::duration<double>(
        Clock::now() - started).count();
    state.candidate_overhead_seconds += event.total_seconds;
    state.candidate_events.push_back(event);
    if (event.submitted) {
        ProgressCallbackState::SubmittedCandidate submitted;
        submitted.event_index = state.candidate_events.size() - 1;
        submitted.values = mapped.values;
        submitted.objective = mapped.objective;
        submitted.confirmed = event.native_objective_returned;
        state.submitted_candidates.push_back(std::move(submitted));
    }
}

void attemptRound60CandidateNoexcept(
    ProgressCallbackState& state,
    void* cbdata,
    int where,
    const std::string& trigger,
    const std::vector<double>* relaxation) noexcept {
    try {
        attemptRound60Candidate(
            state, cbdata, where, trigger, relaxation);
    } catch (...) {
        state.candidate_disabled_after_failure = true;
        try {
            FixedIntervalCandidateEvent event;
            event.event_sequence = ++state.candidate_trigger_count;
            event.callback_where = where;
            event.trigger = trigger;
            event.mode = state.candidate_mode;
            event.status =
                "candidate_exception_caught_and_heuristic_disabled";
            event.acceptance = "not_submitted";
            state.candidate_events.push_back(std::move(event));
        } catch (...) {
            // Never allow optional research telemetry to escape Gurobi's C
            // callback boundary.
        }
    }
}

int __stdcall progressAndBoundTargetCallback(
    GRBmodel* model, void* cbdata, int where, void* usrdata) {
    auto* state = static_cast<ProgressCallbackState*>(usrdata);
    if (!state || !state->api) return 0;
    if(state->round61_session && where==GRB_CB_MIP && !state->submitted_candidates.empty()) {
        double incumbent=GRB_INFINITY;
        if(state->api->cbget(cbdata,where,GRB_CB_MIP_OBJBST,&incumbent)==0 && finiteNative(incumbent))
            for(const auto& submitted:state->submitted_candidates) {
                auto& e=state->candidate_events[submitted.event_index];
                if(incumbent<=submitted.objective+1e-8 &&
                    (!e.native_incumbent_before_available || incumbent<e.native_incumbent_before_submission-1e-8))
                    e.native_incumbent_change_observed=true;
            }
    }
    if (where == GRB_CB_MIP && state->candidate_mode != "off" &&
        !state->candidate_data_triggered &&
        !state->candidate_disabled_after_failure) {
        state->candidate_data_triggered = true;
        attemptRound60CandidateNoexcept(
            *state, cbdata, where,
            "first_eligible_MIP_before_incumbent", nullptr);
    }
    if (where == GRB_CB_MIPSOL && !state->submitted_candidates.empty()) {
        std::vector<double> solution(state->candidate_domain.names.size());
        if (!solution.empty() && state->api->cbget(
                cbdata, where, GRB_CB_MIPSOL_SOL, solution.data()) == 0) {
            for (auto& submitted : state->submitted_candidates) {
                if ((submitted.confirmed && !state->round61_session) ||
                    submitted.values.size() != solution.size() ||
                    submitted.event_index >= state->candidate_events.size()) {
                    continue;
                }
                double maximum_difference = 0.0;
                for (std::size_t index = 0; index < solution.size(); ++index) {
                    maximum_difference = std::max(
                        maximum_difference,
                        std::fabs(solution[index] - submitted.values[index]));
                }
                if (maximum_difference <= 1e-6) {
                    submitted.confirmed = true;
                    auto& event = state->candidate_events[
                        submitted.event_index];
                    event.acceptance =
                        "confirmed_exact_vector_observed_in_MIPSOL";
                    event.exact_vector_observed_in_mipsol = true;
                    event.status = "submitted_and_observed_in_MIPSOL";
                }
            }
        }
    }
    if (where == GRB_CB_MIPNODE &&
        (state->round59_samples || (state->candidate_mode != "off" &&
            !state->round61_session && state->candidate_root_triggers < 2 &&
            !state->candidate_disabled_after_failure))) {
        const auto sample_started = Clock::now();
        if (state->round59_samples) ++state->round59_sample_checks;
        int status = 0;
        double node = 0;
        if (state->api->cbget(cbdata, where, GRB_CB_MIPNODE_STATUS, &status) == 0 &&
            status == GRB_OPTIMAL &&
            state->api->cbget(cbdata, where, GRB_CB_MIPNODE_NODCNT, &node) == 0) {
            const int sampling_bucket = node < 10 ? 1 : node < 100 ? 2 : 3;
            const bool need_values = node < .5 ||
                (state->round59_samples && !state->round59_sampled.count(sampling_bucket));
            std::vector<double> values(need_values ? state->round59_names.size() : 0);
            if (need_values && state->api->cbget(
                    cbdata, where, GRB_CB_MIPNODE_REL, values.data()) == 0) {
                if (node < 0.5) {
                    ++state->round59_root_callback_sequence;
                    if (state->round59_samples) {
                        if (state->round59_first_root_values.empty()) {
                            state->round59_first_root_values = values;
                        }
                        state->round59_latest_root_values = values;
                        ProgressCallbackState::RootScalar scalar;
                        scalar.callback_sequence =
                            state->round59_root_callback_sequence;
                        scalar.node_count = node;
                        state->api->cbget(
                            cbdata, where, GRB_CB_MIPNODE_OBJBND,
                            &scalar.relaxation_objective);
                        scalar.incumbent_available = state->api->cbget(
                            cbdata, where, GRB_CB_MIPNODE_OBJBST,
                            &scalar.incumbent) == 0 &&
                            finiteNative(scalar.incumbent);
                        state->round59_root_scalars.push_back(scalar);
                    }
                    if (state->candidate_mode != "off" &&
                        !state->round61_session &&
                        state->candidate_root_triggers < 2 &&
                        !state->candidate_disabled_after_failure) {
                        ++state->candidate_root_triggers;
                        attemptRound60CandidateNoexcept(
                            *state, cbdata, where,
                            "optimal_root_MIPNODE_cut_pass_" +
                                std::to_string(
                                    state->round59_root_callback_sequence),
                            &values);
                    }
                } else if (state->round59_samples) {
                    state->round59_nonroot_observed = true;
                    const int bucket = node < 10 ? 1 : node < 100 ? 2 : 3;
                    if (!state->round59_sampled.count(bucket)) {
                        state->round59_sampled.insert(bucket);
                        state->round59_nonroot_values.push_back(
                            {bucket, values});
                    }
                }
                if (state->round59_samples) {
                    ++state->round59_sample_successes;
                }
            }
        }
        if (state->round59_samples) {
            state->round59_sample_seconds +=
                std::chrono::duration<double>(Clock::now()-sample_started).count();
        }
    }
    if (where == GRB_CB_MIPNODE && state->round53_mipnode_path_active &&
        !state->tailored_cut_disabled_after_failure) {
        const auto callback_started = Clock::now();
        ++state->round53_mipnode_calls;
        try {
            int node_status = 0;
            double node_count = 0.0;
            ++state->round53_mipnode_status_reads;
            const int status_rc = state->api->cbget(
                cbdata, where, GRB_CB_MIPNODE_STATUS, &node_status);
            const int node_rc = state->api->cbget(
                cbdata, where, GRB_CB_MIPNODE_NODCNT, &node_count);
            if (status_rc != 0 || node_status != GRB_OPTIMAL) {
                ++state->cut_nonoptimal_mipnode_callbacks;
            } else if (node_rc != 0 || !std::isfinite(node_count)) {
                ++state->cut_relaxation_vector_failures;
            } else {
                const bool root_node = node_count < 0.5;
                if (state->round53_separator_active &&
                    state->round53_relaxation_vector_active &&
                    round52SeparationPermitted(
                        state->cut_scope, root_node, true)) {
                    state->cut_manager->recordCallback(root_node);
                    if (state->cut_relaxation_values.size() !=
                        state->cut_variable_names.size()) {
                        state->cut_relaxation_values.resize(
                            state->cut_variable_names.size());
                    }
                    ++state->round53_relaxation_vector_reads;
                    const int relaxation_rc = state->api->cbget(
                        cbdata, where, GRB_CB_MIPNODE_REL,
                        state->cut_relaxation_values.data());
                    if (relaxation_rc != 0) {
                        ++state->cut_relaxation_vector_failures;
                    } else {
                        Round52CutSeparationInput input;
                        input.instance = state->cut_instance;
                        input.interval_id = state->cut_interval_id;
                        input.node_context = root_node
                            ? "optimal_root_MIPNODE"
                            : "optimal_tree_MIPNODE";
                        input.root_node = root_node;
                        input.optimal_relaxation = true;
                        input.maximum_support_rank = state->cut_support_rank;
                        input.certificate_tolerance =
                            state->cut_certificate_tolerance;
                        input.model_variable_mapping =
                            state->cut_variable_indices;
                        for (std::size_t index = 0;
                             index < state->cut_variable_names.size(); ++index) {
                            const std::string& name =
                                state->cut_variable_names[index];
                            if (name.rfind("p_", 0) != 0 &&
                                name.rfind("z_", 0) != 0) {
                                continue;
                            }
                            input.lp_values.emplace(
                                name, state->cut_relaxation_values[index]);
                            input.effective_lower_bounds.emplace(
                                name, state->cut_lower_bounds[index]);
                            input.effective_upper_bounds.emplace(
                                name, state->cut_upper_bounds[index]);
                        }
                        ++state->round53_separator_calls;
                        std::vector<Round52CutCandidate> selected =
                            state->cut_manager->process(
                                state->cut_separator->separate(input));
                        if (state->round53_cut_submission_active) {
                            Round52GurobiCutAdapter adapter(
                                state->cut_variable_indices,
                                [&](int length, const int* indices,
                                    const double* values, char sense,
                                    double rhs) {
                                    return state->api->cbcut(
                                        cbdata, length,
                                        const_cast<int*>(indices),
                                        const_cast<double*>(values), sense,
                                        rhs);
                                });
                            for (const auto& candidate : selected) {
                                ++state->round53_cut_submission_calls;
                                const bool added = adapter.submit(candidate);
                                state->cut_manager->recordSubmission(
                                    candidate, added);
                            }
                            state->cut_adapter_failures +=
                                adapter.telemetry().failures;
                        } else {
                            for (const auto& candidate : selected) {
                                state->cut_manager->recordDryRunSelection(
                                    candidate);
                            }
                        }
                    }
                }
            }
        } catch (...) {
            if (state->cut_manager) {
                state->cut_manager->recordCallbackFailure();
            }
            state->tailored_cut_disabled_after_failure = true;
        }
        state->cut_callback_overhead_seconds +=
            std::chrono::duration<double>(
                Clock::now() - callback_started).count();
        return 0;
    }
    if (where != GRB_CB_MIP) return 0;
    ++state->progress.callback_invocations;
    GurobiProgressEvent event;
    event.callback_where = where;
    event.context = "MIP";
    double native_wall_runtime_seconds = 0.0;
    if (state->api->cbget(cbdata, where, GRB_CB_RUNTIME,
                          &native_wall_runtime_seconds) != 0) return 0;
    // GRB_CB_RUNTIME is wall-clock time.  A host clock correction can make
    // consecutive values decrease even though callback/event order is valid.
    // Trace timing is telemetry only, so use this process's monotonic clock
    // for event placement.  Native runtime remains available from Gurobi's
    // final Runtime attribute and native log.
    event.elapsed_runtime_seconds = std::max(
        0.0, std::chrono::duration<double>(
            Clock::now() - state->telemetry_start).count());
    state->api->cbget(cbdata, where, GRB_CB_WORK, &event.work);
    state->api->cbget(cbdata, where, GRB_CB_MIP_OBJBST, &event.incumbent);
    const bool native_bound_read = state->api->cbget(cbdata, where, GRB_CB_MIP_OBJBND, &event.best_bound)==0;
    state->api->cbget(cbdata, where, GRB_CB_MIP_NODCNT,
                      &event.processed_nodes);
    state->api->cbget(cbdata, where, GRB_CB_MIP_NODLFT, &event.open_nodes);
    // Gurobi's C callback contract returns an int here (not a double).
    // This field is telemetry only; incumbent/bound decisions use the
    // independently read objective values below.
    int callback_solution_count = 0;
    if (state->api->cbget(cbdata, where, GRB_CB_MIP_SOLCNT,
                         &callback_solution_count) == 0) {
        event.solution_count = callback_solution_count;
    }
    state->api->cbget(cbdata, where, GRB_CB_MIP_PHASE, &event.phase);
    event.incumbent_available = finiteNative(event.incumbent);
    event.best_bound_available = native_bound_read && finiteNative(event.best_bound);
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
    if (state->round62_external_stop && event.best_bound_available &&
        !state->round62_external_termination_requested) {
        try {
            if (state->round62_external_stop(event.best_bound) && model && state->api->terminate) {
                state->round62_external_termination_requested=true;
                state->api->terminate(model);
            }
        } catch (...) { state->round62_external_stop={}; }
    }
    if (state->bound_target_enabled && event.best_bound_available &&
        event.best_bound + state->bound_target_tolerance >=
            state->bound_target) {
        state->bound_target_reached = true;
        if (!state->bound_target_termination_requested && model &&
            state->api->terminate) {
            state->bound_target_termination_requested = true;
            state->api->terminate(model);
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
    bool presolved_size_available = false;
    long long presolved_rows = 0;
    long long presolved_columns = 0;
    long long presolved_nonzeros = 0;
    bool root_relaxation_bound_available = false;
    double root_relaxation_bound = 0.0;
    double root_runtime_seconds = 0.0;
    double root_simplex_iterations = 0.0;
    std::vector<FixedIntervalCutFamilyEvidence> root_cut_families;
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
    std::smatch presolved;
    const std::regex presolved_pattern(
        R"(presolved:\s*([0-9]+) rows,\s*([0-9]+) columns,\s*([0-9]+) nonzeros)");
    if (std::regex_search(text, presolved, presolved_pattern)) {
        out.presolved_size_available = true;
        out.presolved_rows = std::stoll(presolved[1].str());
        out.presolved_columns = std::stoll(presolved[2].str());
        out.presolved_nonzeros = std::stoll(presolved[3].str());
    }
    std::smatch root;
    const std::regex root_pattern(
        R"(root relaxation:\s*objective\s*([-+0-9.e]+),\s*([0-9]+) iterations,\s*([-+0-9.e]+) seconds)");
    if (std::regex_search(text, root, root_pattern)) {
        out.root_relaxation_bound_available = true;
        out.root_relaxation_bound = std::stod(root[1].str());
        out.root_simplex_iterations = std::stod(root[2].str());
        out.root_runtime_seconds = std::stod(root[3].str());
    }
    std::istringstream lines(text);
    std::string line;
    bool in_cut_block = false;
    const std::regex cut_pattern(R"(^\s*([a-z][a-z0-9 _-]*):\s*([0-9]+)\s*$)");
    while (std::getline(lines, line)) {
        if (line.find("cutting planes:") != std::string::npos) {
            in_cut_block = true;
            continue;
        }
        if (!in_cut_block) continue;
        if (line.empty() || line.find("explored ") != std::string::npos ||
            line.find("thread count") != std::string::npos) {
            if (!out.root_cut_families.empty()) break;
            continue;
        }
        std::smatch cut;
        if (std::regex_match(line, cut, cut_pattern)) {
            FixedIntervalCutFamilyEvidence evidence;
            evidence.family = cut[1].str();
            evidence.count = std::stoll(cut[2].str());
            out.root_cut_families.push_back(std::move(evidence));
        }
    }
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
        const int threads_get_rc =
            api_.getintparam(env_, GRB_INT_PAR_THREADS, &threads);
        const int presolve_get_rc =
            api_.getintparam(env_, GRB_INT_PAR_PRESOLVE, &presolve);
        const int seed_get_rc =
            api_.getintparam(env_, GRB_INT_PAR_SEED, &seed);
        const int rel_get_rc =
            api_.getdblparam(env_, GRB_DBL_PAR_MIPGAP, &rel);
        const int abs_get_rc =
            api_.getdblparam(env_, GRB_DBL_PAR_MIPGAPABS, &abs);
        const bool readbacks = threads_get_rc == 0 &&
            presolve_get_rc == 0 && seed_get_rc == 0 &&
            rel_get_rc == 0 && abs_get_rc == 0;
        configuration_valid_ = threads_rc == 0 && presolve_rc == 0 &&
            seed_rc == 0 && rel_rc == 0 && abs_rc == 0 && readbacks &&
            threads == 1 && presolve == options_.gurobi_presolve &&
            seed == options_.gurobi_seed && rel == 0.0 && abs == 0.0;
        stats_.threads_requested = 1;
        stats_.threads_set_return_code = threads_rc;
        stats_.threads_get_return_code = threads_get_rc;
        stats_.threads_effective = threads;
        stats_.presolve_requested = options_.gurobi_presolve;
        stats_.presolve_set_return_code = presolve_rc;
        stats_.presolve_get_return_code = presolve_get_rc;
        stats_.presolve_effective = presolve;
        stats_.seed_requested = options_.gurobi_seed;
        stats_.seed_set_return_code = seed_rc;
        stats_.seed_get_return_code = seed_get_rc;
        stats_.seed_effective = seed;
        stats_.mip_gap_requested = 0.0;
        stats_.mip_gap_set_return_code = rel_rc;
        stats_.mip_gap_get_return_code = rel_get_rc;
        stats_.mip_gap_effective = rel;
        stats_.mip_gap_abs_requested = 0.0;
        stats_.mip_gap_abs_set_return_code = abs_rc;
        stats_.mip_gap_abs_get_return_code = abs_get_rc;
        stats_.mip_gap_abs_effective = abs;
        stats_.parameter_roundtrip_valid = configuration_valid_;
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
        out.partial_bound_target_mip =
            request.solve_kind ==
                FixedIntervalSolveKind::PaperPartialBoundTargetMip;
        out.terminal_mip =
            request.solve_kind == FixedIntervalSolveKind::PaperTerminalMip;
        out.native_bound_target = request.native_bound_target;
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
        int native_variables = 0;
        int native_rows = 0;
        int native_general_constraints = 0;
        double native_nonzeros = 0.0;
        api_.getintattr(model, GRB_INT_ATTR_NUMVARS, &native_variables);
        api_.getintattr(model, GRB_INT_ATTR_NUMCONSTRS, &native_rows);
        api_.getintattr(
            model, GRB_INT_ATTR_NUMGENCONSTRS,
            &native_general_constraints);
        api_.getdblattr(model, GRB_DBL_ATTR_DNUMNZS, &native_nonzeros);
        out.model_variable_count = std::max(0, native_variables);
        out.model_linear_constraint_count = std::max(0, native_rows);
        out.model_general_constraint_count =
            std::max(0, native_general_constraints);
        out.model_nonzero_count = std::isfinite(native_nonzeros)
            ? static_cast<long long>(std::llround(
                std::max(0.0, native_nonzeros))) : 0;
        std::vector<char> native_types;
        std::vector<std::string> native_names;
        if (native_variables > 0) {
            native_types.resize(static_cast<std::size_t>(native_variables));
            native_names.resize(static_cast<std::size_t>(native_variables));
            if (api_.getcharattrarray(
                    model, GRB_CHAR_ATTR_VTYPE, 0, native_variables,
                    native_types.data()) == 0) {
                for (int index = 0; index < native_variables; ++index) {
                    const char type = native_types[
                        static_cast<std::size_t>(index)];
                    if (type == GRB_BINARY) {
                        ++out.model_binary_variable_count;
                    } else if (type == GRB_INTEGER ||
                               type == GRB_SEMIINT) {
                        ++out.model_integer_variable_count;
                    } else {
                        ++out.model_continuous_variable_count;
                    }
                    char* name = nullptr;
                    if (api_.getstrattrelement(
                            model, GRB_STR_ATTR_VARNAME, index, &name) == 0 &&
                        name) {
                        native_names[static_cast<std::size_t>(index)] = name;
                    }
                }
            }
        }
        out.interval_mip_policy = request.interval_mip_policy;
        const Round50IntervalMipPolicy round50_policy =
            parseRound50IntervalMipPolicy(request.interval_mip_policy);
        if (!round50_policy.valid) {
            out.failure_reason = round50_policy.failure_reason;
            return out;
        }
        if (!request.additional_linear_rows.empty()) {
            out.additional_linear_rows_attempted = true;
            if (retained) {
                out.additional_linear_rows_status =
                    "additional_rows_require_fresh_canonical_model";
                out.failure_reason = out.additional_linear_rows_status;
                return out;
            }
            std::unordered_map<std::string, int> indices;
            bool rows_valid = native_names.size() ==
                static_cast<std::size_t>(native_variables);
            for (int index = 0; rows_valid && index < native_variables;
                 ++index) {
                const std::string& name = native_names[
                    static_cast<std::size_t>(index)];
                rows_valid = !name.empty() &&
                    indices.emplace(name, index).second;
            }
            std::set<std::string> row_names;
            std::set<std::string> signatures;
            std::ostringstream signature_ledger;
            int add_rc = 0;
            for (std::size_t row_index = 0;
                 rows_valid && row_index < request.additional_linear_rows.size();
                 ++row_index) {
                const auto& row = request.additional_linear_rows[row_index];
                rows_valid = !row.row_name.empty() &&
                    row_names.insert(row.row_name).second &&
                    !row.canonical_signature.empty() &&
                    signatures.insert(row.canonical_signature).second &&
                    row.variable_names.size() == row.coefficients.size() &&
                    !row.variable_names.empty() && std::isfinite(row.rhs) &&
                    (!request.round59_additional_rows_user_pool ||
                     (row.scope == "global" && row.sense != '=')) &&
                    (row.sense == '<' || row.sense == '>' || row.sense == '=');
                std::vector<int> columns;
                std::vector<double> coefficients;
                std::set<std::string> row_variables;
                for (std::size_t term = 0;
                     rows_valid && term < row.variable_names.size(); ++term) {
                    const auto found_index = indices.find(row.variable_names[term]);
                    rows_valid = found_index != indices.end() &&
                        row_variables.insert(row.variable_names[term]).second &&
                        std::isfinite(row.coefficients[term]) &&
                        std::fabs(row.coefficients[term]) > 1e-14;
                    if (rows_valid) {
                        columns.push_back(found_index->second);
                        coefficients.push_back(row.coefficients[term]);
                    }
                }
                if (!rows_valid) break;
                const char native_sense = row.sense == '<'
                    ? GRB_LESS_EQUAL : (row.sense == '>'
                        ? GRB_GREATER_EQUAL : GRB_EQUAL);
                add_rc = api_.addconstr(
                    model, static_cast<int>(columns.size()), columns.data(),
                    coefficients.data(), native_sense, row.rhs,
                    row.row_name.c_str());
                rows_valid = add_rc == 0;
                if (rows_valid) {
                    if (row_index) signature_ledger << ';';
                    signature_ledger << row.canonical_signature;
                    ++out.additional_linear_rows_added;
                }
            }
            const int update_rc = rows_valid ? api_.updatemodel(model) : add_rc;
            int rows_after = -1;
            const bool row_count_valid = rows_valid && update_rc == 0 &&
                api_.getintattr(model, GRB_INT_ATTR_NUMCONSTRS, &rows_after) == 0 &&
                rows_after == native_rows +
                    static_cast<int>(request.additional_linear_rows.size());
            out.additional_linear_rows_valid = rows_valid && row_count_valid &&
                out.additional_linear_rows_added == static_cast<long long>(
                    request.additional_linear_rows.size());
            out.additional_linear_row_signatures = signature_ledger.str();
            out.additional_linear_rows_status = out.additional_linear_rows_valid
                ? "added_to_fresh_model_and_count_read_back"
                : (!rows_valid ? "invalid_or_unaddable_linear_row"
                               : "linear_row_count_readback_failed");
            if (!out.additional_linear_rows_valid) {
                out.failure_reason = out.additional_linear_rows_status;
                return out;
            }
            out.native_model_modified = true;
            out.model_linear_constraint_count = rows_after;
            if (request.round59_additional_rows_user_pool) {
                const int count = static_cast<int>(request.additional_linear_rows.size());
                std::vector<int> lazy(static_cast<std::size_t>(count), -1);
                std::vector<int> readback(static_cast<std::size_t>(count), 0);
                if (api_.setintattrarray(model, GRB_INT_ATTR_LAZY,
                        native_rows, count, lazy.data()) != 0 ||
                    api_.updatemodel(model) != 0 ||
                    api_.getintattrarray(model, GRB_INT_ATTR_LAZY,
                        native_rows, count, readback.data()) != 0 || readback != lazy) {
                    out.failure_reason = "round59_user_pool_attribute_readback_failed";
                    return out;
                }
                out.additional_linear_rows_status = "round59_Lazy_minus1_readback_valid";
            }
        } else {
            out.additional_linear_rows_valid = true;
        }
        if (request.round59_mip_focus != -1) {
            int readback = -1;
            if ((request.round59_mip_focus != 1 && request.round59_mip_focus != 3) ||
                api_.setintparam(model_env, GRB_INT_PAR_MIPFOCUS, request.round59_mip_focus) != 0 ||
                api_.getintparam(model_env, GRB_INT_PAR_MIPFOCUS, &readback) != 0 ||
                readback != request.round59_mip_focus) {
                out.failure_reason = "round59_mip_focus_readback_failed";
                return out;
            }
        }
        std::vector<FixedIntervalMipRequest::VariableBoundOverride>
            effective_bound_overrides = request.variable_bound_overrides;
        if (!request.round60_fixed_inventory.empty()) {
            bool fixed_inventory_valid = request.round60_fixed_inventory.size() ==
                static_cast<std::size_t>(instance_.V + 1);
            for (int station = 1; fixed_inventory_valid &&
                 station <= instance_.V; ++station) {
                fixed_inventory_valid =
                    request.round60_fixed_inventory[station] >= 0 &&
                    request.round60_fixed_inventory[station] <=
                        instance_.capacity[station];
            }
            if (!fixed_inventory_valid) {
                out.failure_reason = "round60_fixed_inventory_invalid";
                return out;
            }
            for (const std::string& name : native_names) {
                int station = 0;
                int bit = 0;
                bool selected = parseSingleIndex(name, "Y_", station) &&
                    station >= 1 && station <= instance_.V;
                double fixed_value = selected
                    ? request.round60_fixed_inventory[station] : 0.0;
                if (!selected && parseTwoIndices(name, "bit_", station, bit) &&
                    station >= 1 && station <= instance_.V &&
                    bit >= 0 && bit < 63) {
                    selected = true;
                    fixed_value =
                        (request.round60_fixed_inventory[station] >> bit) & 1;
                }
                if (selected) {
                    FixedIntervalMipRequest::VariableBoundOverride fixed;
                    fixed.variable_name = name;
                    fixed.lower_bound_enabled = true;
                    fixed.lower_bound = fixed_value;
                    fixed.upper_bound_enabled = true;
                    fixed.upper_bound = fixed_value;
                    effective_bound_overrides.push_back(std::move(fixed));
                }
            }
        }
        if (!effective_bound_overrides.empty()) {
            out.variable_bound_override_attempted = true;
            out.variable_bound_override_count = static_cast<long long>(
                effective_bound_overrides.size());
            std::unordered_map<std::string, int> indices;
            bool override_valid = native_names.size() ==
                static_cast<std::size_t>(native_variables);
            for (int index = 0; override_valid && index < native_variables;
                 ++index) {
                const std::string& name = native_names[
                    static_cast<std::size_t>(index)];
                override_valid = !name.empty() &&
                    indices.emplace(name, index).second;
            }
            std::vector<double> lower(
                static_cast<std::size_t>(native_variables));
            std::vector<double> upper(
                static_cast<std::size_t>(native_variables));
            override_valid = override_valid &&
                api_.getdblattrarray(model, GRB_DBL_ATTR_LB, 0,
                    native_variables, lower.data()) == 0 &&
                api_.getdblattrarray(model, GRB_DBL_ATTR_UB, 0,
                    native_variables, upper.data()) == 0;
            std::set<std::string> requested_names;
            for (const auto& override_value :
                    effective_bound_overrides) {
                const auto found_index = indices.find(
                    override_value.variable_name);
                override_valid = override_valid &&
                    !override_value.variable_name.empty() &&
                    found_index != indices.end() &&
                    requested_names.insert(
                        override_value.variable_name).second &&
                    (override_value.lower_bound_enabled ||
                     override_value.upper_bound_enabled) &&
                    (!override_value.lower_bound_enabled ||
                     std::isfinite(override_value.lower_bound)) &&
                    (!override_value.upper_bound_enabled ||
                     std::isfinite(override_value.upper_bound));
                if (!override_valid) break;
                const std::size_t index = static_cast<std::size_t>(
                    found_index->second);
                if (override_value.lower_bound_enabled) {
                    lower[index] = override_value.lower_bound;
                }
                if (override_value.upper_bound_enabled) {
                    upper[index] = override_value.upper_bound;
                }
                override_valid = lower[index] <= upper[index] + 1e-12;
                if (!override_valid) break;
            }
            const int lower_rc = override_valid
                ? api_.setdblattrarray(model, GRB_DBL_ATTR_LB, 0,
                      native_variables, lower.data()) : -1;
            const int upper_rc = lower_rc == 0
                ? api_.setdblattrarray(model, GRB_DBL_ATTR_UB, 0,
                      native_variables, upper.data()) : lower_rc;
            const int update_rc = upper_rc == 0
                ? api_.updatemodel(model) : upper_rc;
            std::vector<double> read_lower(
                static_cast<std::size_t>(native_variables));
            std::vector<double> read_upper(
                static_cast<std::size_t>(native_variables));
            bool readback = update_rc == 0 &&
                api_.getdblattrarray(model, GRB_DBL_ATTR_LB, 0,
                    native_variables, read_lower.data()) == 0 &&
                api_.getdblattrarray(model, GRB_DBL_ATTR_UB, 0,
                    native_variables, read_upper.data()) == 0;
            for (int index = 0; readback && index < native_variables;
                 ++index) {
                const std::size_t offset = static_cast<std::size_t>(index);
                readback = read_lower[offset] == lower[offset] &&
                    read_upper[offset] == upper[offset];
            }
            out.variable_bound_override_readback_valid =
                override_valid && readback;
            out.variable_bound_override_status =
                out.variable_bound_override_readback_valid
                    ? "applied_and_read_back"
                    : (!override_valid ? "invalid_override_request"
                       : "gurobi_bound_override_or_readback_failed");
            if (!out.variable_bound_override_readback_valid) {
                out.failure_reason = out.variable_bound_override_status;
                return out;
            }
        } else {
            out.variable_bound_override_readback_valid = true;
            out.variable_bound_override_status = "not_requested";
        }
        const bool explicit_sparse_priorities =
            !request.branch_priority_overrides.empty();
        if (!out.lp_relaxation &&
            (explicit_sparse_priorities ||
             round50_policy.branching != Round50BranchingPolicy::Default)) {
            out.branch_priority_assignment_attempted = true;
            std::vector<int> priorities(
                static_cast<std::size_t>(native_variables), 0);
            bool registry_valid = native_types.size() == priorities.size() &&
                native_names.size() == priorities.size();
            if (explicit_sparse_priorities &&
                round50_policy.branching != Round50BranchingPolicy::Default) {
                registry_valid = false;
            }
            if (explicit_sparse_priorities) {
                registry_valid = registry_valid &&
                    request.branch_priority_overrides.size() <= 2;
                std::unordered_map<std::string, int> indices;
                for (int index = 0; registry_valid &&
                     index < native_variables; ++index) {
                    registry_valid = !native_names[
                        static_cast<std::size_t>(index)].empty() &&
                        indices.emplace(native_names[
                            static_cast<std::size_t>(index)], index).second;
                }
                std::set<std::string> selected;
                for (const auto& override_value :
                        request.branch_priority_overrides) {
                    const auto found_index = indices.find(
                        override_value.variable_name);
                    registry_valid = registry_valid &&
                        found_index != indices.end() &&
                        selected.insert(
                            override_value.variable_name).second &&
                        (override_value.priority == 1 ||
                         override_value.priority == 2);
                    if (!registry_valid) break;
                    const int index = found_index->second;
                    const char type = native_types[
                        static_cast<std::size_t>(index)];
                    const Round50VariableFamily family =
                        classifyRound50Variable(
                            override_value.variable_name);
                    registry_valid =
                        (type == GRB_BINARY || type == GRB_INTEGER) &&
                        family != Round50VariableFamily::Auxiliary;
                    if (!registry_valid) break;
                    priorities[static_cast<std::size_t>(index)] =
                        override_value.priority;
                    FixedIntervalBranchPriorityEvidence evidence;
                    evidence.variable_name = override_value.variable_name;
                    evidence.semantic_family =
                        round50VariableFamilyName(family);
                    evidence.variable_type = type;
                    evidence.assigned_priority = override_value.priority;
                    out.branch_priority_evidence.push_back(
                        std::move(evidence));
                }
            } else {
                for (int index = 0; registry_valid &&
                     index < native_variables; ++index) {
                    const char type = native_types[
                        static_cast<std::size_t>(index)];
                    if (type != GRB_BINARY && type != GRB_INTEGER &&
                        type != GRB_SEMIINT) {
                        continue;
                    }
                    const std::string& name = native_names[
                        static_cast<std::size_t>(index)];
                    if (name.empty()) {
                        registry_valid = false;
                        break;
                    }
                    const Round50VariableFamily family =
                        classifyRound50Variable(name);
                    const int priority = round50BranchPriority(
                        round50_policy.branching, family);
                    if (priority <= 0) {
                        registry_valid = false;
                        break;
                    }
                    priorities[static_cast<std::size_t>(index)] = priority;
                    FixedIntervalBranchPriorityEvidence evidence;
                    evidence.variable_name = name;
                    evidence.semantic_family =
                        round50VariableFamilyName(family);
                    evidence.variable_type = type;
                    evidence.assigned_priority = priority;
                    out.branch_priority_evidence.push_back(
                        std::move(evidence));
                }
            }
            const int priority_rc = registry_valid
                ? api_.setintattrarray(
                      model, GRB_INT_ATTR_BRANCHPRIORITY, 0,
                      native_variables, priorities.data())
                : -1;
            const int update_rc = priority_rc == 0
                ? api_.updatemodel(model) : priority_rc;
            std::vector<int> priority_readback(
                static_cast<std::size_t>(native_variables), -1);
            bool readback_valid = update_rc == 0 &&
                api_.getintattrarray(
                    model, GRB_INT_ATTR_BRANCHPRIORITY, 0,
                    native_variables, priority_readback.data()) == 0;
            long long zero_count = 0;
            for (int index = 0; readback_valid &&
                 index < native_variables; ++index) {
                const int expected = priorities[
                    static_cast<std::size_t>(index)];
                const int observed = priority_readback[
                    static_cast<std::size_t>(index)];
                readback_valid = observed == expected;
                if (observed == 0) ++zero_count;
            }
            out.branch_priority_zero_readback_count = zero_count;
            out.branch_priority_assignment_valid =
                registry_valid && priority_rc == 0 && update_rc == 0 &&
                readback_valid;
            out.branch_priority_assigned_count =
                static_cast<long long>(out.branch_priority_evidence.size());
            out.branch_priority_assignment_status =
                out.branch_priority_assignment_valid ? "applied"
                : (!registry_valid ? "semantic_registry_failed"
                   : "gurobi_branch_priority_attribute_or_readback_failed");
            if (!out.branch_priority_assignment_valid) {
                out.failure_reason = out.branch_priority_assignment_status;
                return out;
            }
        } else {
            out.branch_priority_assignment_valid = true;
            out.branch_priority_assignment_status = "default_no_assignment";
        }
        auto readRange = [&](const char* min_attr, const char* max_attr,
                             double& minimum, double& maximum) {
            return api_.getdblattr(model, min_attr, &minimum) == 0 &&
                api_.getdblattr(model, max_attr, &maximum) == 0 &&
                std::isfinite(minimum) && std::isfinite(maximum);
        };
        out.numerical_ranges_available =
            readRange(GRB_DBL_ATTR_MIN_COEFF, GRB_DBL_ATTR_MAX_COEFF,
                      out.minimum_matrix_coefficient,
                      out.maximum_matrix_coefficient) &&
            readRange(GRB_DBL_ATTR_MIN_OBJ_COEFF, GRB_DBL_ATTR_MAX_OBJ_COEFF,
                      out.minimum_objective_coefficient,
                      out.maximum_objective_coefficient) &&
            readRange(GRB_DBL_ATTR_MIN_BOUND, GRB_DBL_ATTR_MAX_BOUND,
                      out.minimum_variable_bound,
                      out.maximum_variable_bound) &&
            readRange(GRB_DBL_ATTR_MIN_RHS, GRB_DBL_ATTR_MAX_RHS,
                      out.minimum_rhs, out.maximum_rhs);
        if (out.lp_relaxation) {
            int variable_count = 0;
            if (api_.getintattr(model, GRB_INT_ATTR_NUMVARS,
                                &variable_count) != 0 || variable_count <= 0) {
                out.failure_reason = "paper_lp_variable_count_unavailable";
                return out;
            }
            if ((request.incremental_model_reuse_enabled ||
                 request.capture_lp_primal_dual_evidence) &&
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
            if (request.capture_lp_primal_dual_evidence) {
                out.lp_primal_dual_variable_evidence.resize(
                    static_cast<std::size_t>(variable_count));
                std::vector<double> lower(
                    static_cast<std::size_t>(variable_count));
                std::vector<double> upper(
                    static_cast<std::size_t>(variable_count));
                bool metadata_ok = state.original_variable_types.size() ==
                        static_cast<std::size_t>(variable_count) &&
                    api_.getdblattrarray(model, GRB_DBL_ATTR_LB, 0,
                        variable_count, lower.data()) == 0 &&
                    api_.getdblattrarray(model, GRB_DBL_ATTR_UB, 0,
                        variable_count, upper.data()) == 0;
                for (int index = 0; metadata_ok && index < variable_count;
                     ++index) {
                    char* name = nullptr;
                    metadata_ok = api_.getstrattrelement(
                        model, GRB_STR_ATTR_VARNAME, index, &name) == 0 &&
                        name && *name;
                    if (metadata_ok) {
                        auto& evidence = out.lp_primal_dual_variable_evidence[
                            static_cast<std::size_t>(index)];
                        evidence.name = name;
                        evidence.original_type = state.original_variable_types[
                            static_cast<std::size_t>(index)];
                        evidence.lower_bound = lower[
                            static_cast<std::size_t>(index)];
                        evidence.upper_bound = upper[
                            static_cast<std::size_t>(index)];
                    }
                }
                if (!metadata_ok) {
                    out.lp_primal_dual_variable_evidence.clear();
                }
                out.lp_verified_cutoff = request.verified_cutoff;
                out.lp_model_fingerprint =
                    request.canonical_model_fingerprint;
                int objective_sense = 0;
                if (api_.getintattr(model, GRB_INT_ATTR_MODELSENSE,
                                    &objective_sense) == 0) {
                    out.lp_objective_sense = objective_sense;
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

        out.tailored_cut_policy = round50_policy.tailored_cut_policy;
        out.round53_callback_mode = round50_policy.round53_callback_mode;
        out.gurobi_cbcut_symbol_loaded = api_.cbcut != nullptr;
        out.gurobi_cblazy_symbol_loaded = api_.cblazy != nullptr;
        const bool round53_precrush_active = out.terminal_mip &&
            round53CallbackPreCrushEnabled(round50_policy);
        const bool round53_mipnode_active = out.terminal_mip &&
            round53CallbackMipNodeEnabled(round50_policy);
        const bool tailored_cut_active = out.terminal_mip &&
            round53CallbackSeparatorEnabled(round50_policy);
        const bool cut_submission_active = out.terminal_mip &&
            round53CallbackSubmissionEnabled(round50_policy);
        Round52SupportDurationSeparator cut_separator;
        Round52CutManager cut_manager;
        if (round53_precrush_active) {
            out.gurobi_precrush_requested =
                round52RequiredGurobiPreCrush();
            out.gurobi_precrush_set_return_code = api_.setintparam(
                model_env, GRB_INT_PAR_PRECRUSH,
                out.gurobi_precrush_requested);
            out.gurobi_precrush_get_return_code = api_.getintparam(
                model_env, GRB_INT_PAR_PRECRUSH,
                &out.gurobi_precrush_effective);
            out.gurobi_precrush_roundtrip_valid =
                out.gurobi_precrush_set_return_code == 0 &&
                out.gurobi_precrush_get_return_code == 0 &&
                out.gurobi_precrush_effective ==
                    out.gurobi_precrush_requested;
            if (!out.gurobi_precrush_roundtrip_valid ||
                (cut_submission_active &&
                 !out.gurobi_cbcut_symbol_loaded)) {
                out.failure_reason =
                    "round53_gurobi_callback_capability_invalid";
                return out;
            }
        }
        if (tailored_cut_active) {
            cut_manager.beginModel(
                request.canonical_model_fingerprint + "|" +
                request.leaf_id);
        }

        ProgressCallbackState callback;
        std::ofstream round59_samples;
        if (!request.round59_node_samples_path.empty() && out.terminal_mip) {
            round59_samples.open(request.round59_node_samples_path);
            if (!round59_samples) {
                out.failure_reason = "round59_sample_output_open_failed";
                return out;
            }
            round59_samples.precision(17);
            round59_samples << "sample_kind,root_callback_sequence,"
                "node_bucket,node_count,root_completion_status,variable,value\n";
            callback.round59_samples = &round59_samples;
            callback.round59_names = native_names;
        }
        callback.api = &api_;
        if (!out.lp_relaxation) callback.round62_external_stop=request.round62_external_stop;
        out.gurobi_cbsolution_symbol_loaded = api_.cbsolution != nullptr;
        out.round60_candidate_mode = request.round60_candidate_mode;
        const bool round60_candidate_active = (out.terminal_mip ||
            (request.round61_session && out.partial_bound_target_mip)) &&
            request.round60_candidate_mode != "off";
        if (request.round60_candidate_mode != "off" &&
            request.round60_candidate_mode != "dry" &&
            request.round60_candidate_mode != "inject") {
            out.failure_reason = "invalid_round60_candidate_mode";
            return out;
        }
        if (round60_candidate_active) {
            callback.round61_session = request.round61_session;
            callback.candidate_instance = &instance_;
            callback.candidate_options = &options_;
            callback.candidate_mode = request.round60_candidate_mode;
            callback.candidate_model_identity =
                request.canonical_model_fingerprint + "|" + request.leaf_id;
            callback.candidate_gamma_L = request.gamma_L;
            callback.candidate_gamma_U = request.gamma_U;
            callback.candidate_cutoff = request.verified_cutoff;
            callback.candidate_maximum_evaluations =
                std::max(1, request.round60_candidate_maximum_evaluations);
            callback.candidate_maximum_stations =
                std::max(1, request.round60_candidate_maximum_stations);
            callback.candidate_domain.names = native_names;
            callback.candidate_domain.variable_types = native_types;
            callback.candidate_domain.lower_bounds.resize(
                static_cast<std::size_t>(native_variables));
            callback.candidate_domain.upper_bounds.resize(
                static_cast<std::size_t>(native_variables));
            const bool candidate_registry_valid = api_.cbsolution != nullptr &&
                native_names.size() == static_cast<std::size_t>(native_variables) &&
                native_types.size() == static_cast<std::size_t>(native_variables) &&
                api_.getdblattrarray(
                    model, GRB_DBL_ATTR_LB, 0, native_variables,
                    callback.candidate_domain.lower_bounds.data()) == 0 &&
                api_.getdblattrarray(
                    model, GRB_DBL_ATTR_UB, 0, native_variables,
                    callback.candidate_domain.upper_bounds.data()) == 0 &&
                out.model_general_constraint_count == 0 &&
                readLinearModel(api_, model, native_variables, native_rows,
                                callback.candidate_linear_model);
            if (!candidate_registry_valid) {
                callback.candidate_disabled_after_failure = true;
                callback.candidate_mode = "off";
                FixedIntervalCandidateEvent event;
                event.event_sequence = 1;
                event.mode = request.round60_candidate_mode;
                event.status =
                    "optional_candidate_registry_invalid_base_solve_preserved";
                callback.candidate_events.push_back(std::move(event));
            } else {
                callback.round59_names = native_names;
                out.round60_candidate_callback_active = true;
            }
        }
        callback.bound_target_enabled =
            out.partial_bound_target_mip &&
            request.native_bound_target_enabled;
        callback.bound_target = request.native_bound_target;
        callback.bound_target_tolerance =
            std::max(0.0, request.native_bound_target_tolerance);
        callback.round53_mipnode_path_active = round53_mipnode_active;
        callback.round53_relaxation_vector_active =
            out.terminal_mip &&
            round53CallbackRelaxationEnabled(round50_policy);
        callback.round53_separator_active = tailored_cut_active;
        callback.round53_cut_submission_active = cut_submission_active;
        callback.tailored_cut_active = tailored_cut_active;
        if (tailored_cut_active) {
            callback.cut_instance = &instance_;
            callback.cut_separator = &cut_separator;
            callback.cut_manager = &cut_manager;
            callback.cut_scope = round50_policy.tailored_cut_policy ==
                    "sd-r3-tree-blockmax"
                ? Round52CutSeparationScope::AllOptimalTreeNodes
                : Round52CutSeparationScope::RootOnly;
            callback.cut_support_rank =
                round50_policy.tailored_cut_support_rank;
            callback.cut_certificate_tolerance = 1e-7;
            callback.cut_interval_id = request.leaf_id;
            callback.cut_variable_names = native_names;
            callback.cut_lower_bounds.resize(
                static_cast<std::size_t>(native_variables));
            callback.cut_upper_bounds.resize(
                static_cast<std::size_t>(native_variables));
            bool cut_registry_valid =
                callback.cut_variable_names.size() ==
                    static_cast<std::size_t>(native_variables) &&
                api_.getdblattrarray(
                    model, GRB_DBL_ATTR_LB, 0, native_variables,
                    callback.cut_lower_bounds.data()) == 0 &&
                api_.getdblattrarray(
                    model, GRB_DBL_ATTR_UB, 0, native_variables,
                    callback.cut_upper_bounds.data()) == 0;
            for (int index = 0; cut_registry_valid &&
                 index < native_variables; ++index) {
                const std::string& name = callback.cut_variable_names[
                    static_cast<std::size_t>(index)];
                cut_registry_valid = !name.empty() &&
                    callback.cut_variable_indices.emplace(
                        name, index).second;
            }
            if (!cut_registry_valid) {
                out.failure_reason =
                    "round52_gurobi_cut_variable_registry_invalid";
                return out;
            }
            callback.cut_relaxation_values.resize(
                static_cast<std::size_t>(native_variables));
            out.tailored_cut_callback_active = true;
        }
        const int callback_rc = api_.setcallbackfunc(
            model, progressAndBoundTargetCallback, &callback);
        if (callback_rc != 0) {
            out.failure_reason = apiError(api_, model_env, callback_rc);
            return out;
        }
        out.optimize_return_code = api_.optimize(model);
        if (callback.round59_samples) {
            int post_optimize_status = 0;
            const bool solved_at_root = api_.getintattr(
                model, GRB_INT_ATTR_STATUS, &post_optimize_status) == 0 &&
                post_optimize_status == GRB_OPTIMAL;
            const std::string root_status = callback.round59_nonroot_observed
                ? "confirmed_complete_before_nonroot"
                : (solved_at_root ? "confirmed_complete_at_optimal_termination"
                                  : "last_observed_root_relaxation");
            auto write_sample = [&](const std::string& kind,
                                    long long sequence,
                                    int bucket,
                                    double node_count,
                                    const std::vector<double>& values) {
                for (std::size_t i = 0; i < values.size(); ++i) {
                    *callback.round59_samples << kind << ',' << sequence << ','
                        << bucket << ',' << node_count << ',' << root_status
                        << ',' << callback.round59_names[i] << ','
                        << values[i] << '\n';
                }
            };
            if (!callback.round59_first_root_values.empty()) {
                write_sample("first_root_relaxation", 1, 0, 0.0,
                             callback.round59_first_root_values);
            }
            if (!callback.round59_latest_root_values.empty()) {
                write_sample("latest_root_relaxation",
                             callback.round59_root_callback_sequence, 0, 0.0,
                             callback.round59_latest_root_values);
            }
            for (const auto& sample : callback.round59_nonroot_values) {
                write_sample("bounded_nonroot_relaxation", 0, sample.first,
                             sample.first == 1 ? 1.0
                                 : (sample.first == 2 ? 10.0 : 100.0),
                             sample.second);
            }
            std::ofstream scalars(
                request.round59_node_samples_path.string() +
                ".root_scalars.csv");
            scalars << std::setprecision(17)
                << "root_callback_sequence,node_count,relaxation_objective,"
                   "incumbent_available,incumbent\n";
            for (const auto& scalar : callback.round59_root_scalars) {
                scalars << scalar.callback_sequence << ',' << scalar.node_count
                    << ',' << scalar.relaxation_objective << ','
                    << scalar.incumbent_available << ',' << scalar.incumbent
                    << '\n';
            }
            std::ofstream audit(request.round59_node_samples_path.string()+".audit.json");
            audit.precision(17);
            audit << "{\"sampling_seconds\":" << callback.round59_sample_seconds
                  << ",\"eligible_callback_checks\":" << callback.round59_sample_checks
                  << ",\"successful_samples\":" << callback.round59_sample_successes
                  << ",\"sampling_failures\":"
                  << std::max(0LL, callback.round59_sample_checks -
                                     callback.round59_sample_successes)
                  << ",\"root_callback_count\":"
                  << callback.round59_root_callback_sequence
                  << ",\"root_completion_status\":\"" << root_status << "\""
                  << "}\n";
        }
        if (!callback.submitted_candidates.empty()) {
            int final_solution_count = 0;
            std::vector<double> final_solution(
                callback.candidate_domain.names.size());
            const bool final_solution_available =
                !final_solution.empty() &&
                api_.getintattr(model, GRB_INT_ATTR_SOLCOUNT,
                                &final_solution_count) == 0 &&
                final_solution_count > 0 &&
                api_.getdblattrarray(
                    model, GRB_DBL_ATTR_X, 0,
                    static_cast<int>(final_solution.size()),
                    final_solution.data()) == 0;
            if (final_solution_available) {
                for (auto& submitted : callback.submitted_candidates) {
                    if ((submitted.confirmed && !callback.round61_session) ||
                        submitted.values.size() != final_solution.size() ||
                        submitted.event_index >=
                            callback.candidate_events.size()) {
                        continue;
                    }
                    double maximum_integer_difference = 0.0;
                    int compared_integer_columns = 0;
                    for (std::size_t column = 0;
                         column < final_solution.size(); ++column) {
                        const char type = callback.candidate_domain.
                            variable_types[column];
                        if (type != GRB_BINARY && type != GRB_INTEGER &&
                            type != GRB_SEMIINT) {
                            continue;
                        }
                        ++compared_integer_columns;
                        maximum_integer_difference = std::max(
                            maximum_integer_difference,
                            std::fabs(final_solution[column] -
                                      submitted.values[column]));
                    }
                    if (compared_integer_columns > 0 &&
                        maximum_integer_difference <= 1e-6) {
                        submitted.confirmed = true;
                        auto& event = callback.candidate_events[
                            submitted.event_index];
                        event.acceptance =
                            "confirmed_submitted_integer_decision_vector_"
                            "is_final_native_solution";
                        event.final_integer_vector_matches = true;
                        event.status =
                            "submitted_integer_decisions_match_final_native_"
                            "solution";
                    }
                }
            }
        }
        out.round60_candidate_disabled_after_failure =
            callback.candidate_disabled_after_failure;
        out.round60_candidate_triggers = callback.candidate_trigger_count;
        out.round60_candidate_overhead_seconds =
            callback.candidate_overhead_seconds;
        out.round60_candidate_events = callback.candidate_events;
        for (const auto& event : out.round60_candidate_events) {
            if (event.generated) ++out.round60_candidates_generated;
            if (event.independently_verified) ++out.round60_candidates_verified;
            if (event.mapping_complete && event.linear_constraints_valid) {
                ++out.round60_candidates_mapped;
            }
            if (event.submitted) ++out.round60_candidates_submitted;
            if (event.acceptance.rfind("confirmed_", 0) == 0) {
                ++out.round60_candidates_confirmed_accepted;
            } else if (event.submitted) {
                ++out.round60_candidates_acceptance_unknown;
            }
            if (event.generated &&
                (!out.round60_best_generated_objective_available ||
                 event.candidate_objective <
                     out.round60_best_generated_objective)) {
                out.round60_best_generated_objective_available = true;
                out.round60_best_generated_objective =
                    event.candidate_objective;
            }
        }
        if (!request.round60_candidate_log_path.empty()) {
            bool candidate_log_written = false;
            try {
                if (request.round60_candidate_log_path.has_parent_path()) {
                    std::filesystem::create_directories(
                        request.round60_candidate_log_path.parent_path());
                }
                std::ofstream candidate_log(
                    request.round60_candidate_log_path);
                if (candidate_log) {
                    candidate_log << std::setprecision(17)
                        << "event_sequence,callback_where,trigger,source,content_sha256,"
                           "mode,status,generated,verified,strictly_improves_cutoff,"
                           "mapping_complete,bounds_valid,integrality_valid,"
                           "linear_checked,linear_valid,linear_rows_checked,"
                           "violated_rows,max_violation,"
                           "submitted,submission_return_code,native_objective_returned,"
                           "native_objective,acceptance,objective_evaluations,"
                           "callback_elapsed_seconds,generation_seconds,"
                           "verification_seconds,mapping_seconds,residual_check_seconds,"
                           "total_seconds,candidate_objective,exact_vector_observed_in_mipsol,final_integer_vector_matches,native_incumbent_change_observed,native_incumbent_before_available,native_incumbent_before_submission\n";
                    for (const auto& event : out.round60_candidate_events) {
                        candidate_log << event.event_sequence << ','
                            << event.callback_where << ',' << event.trigger << ','
                            << event.source << ',' << event.content_sha256 << ','
                            << event.mode << ',' << event.status << ','
                            << event.generated << ',' << event.independently_verified
                            << ',' << event.strictly_improves_frozen_cutoff << ','
                            << event.mapping_complete << ',' << event.bounds_valid
                            << ',' << event.integrality_valid << ','
                            << event.linear_constraints_checked << ','
                            << event.linear_constraints_valid << ','
                            << event.linear_rows_checked << ','
                            << event.violated_linear_rows << ','
                            << event.maximum_linear_violation << ',' << event.submitted
                            << ',' << event.submission_return_code << ','
                            << event.native_objective_returned << ','
                            << event.native_objective << ',' << event.acceptance << ','
                            << event.objective_evaluations << ','
                            << event.callback_elapsed_seconds << ','
                            << event.generation_seconds << ','
                            << event.verification_seconds << ','
                            << event.mapping_seconds << ','
                            << event.residual_check_seconds << ','
                            << event.total_seconds << ',' << event.candidate_objective
                            << ',' << event.exact_vector_observed_in_mipsol
                            << ',' << event.final_integer_vector_matches
                            << ',' << event.native_incumbent_change_observed
                            << ',' << event.native_incumbent_before_available
                            << ',' << event.native_incumbent_before_submission
                            << '\n';
                    }
                    candidate_log_written = static_cast<bool>(candidate_log);
                }
            } catch (...) {
                candidate_log_written = false;
            }
            if (!candidate_log_written) {
                out.round60_candidate_disabled_after_failure = true;
            }
        }
        out.round53_mipnode_calls = callback.round53_mipnode_calls;
        out.round53_mipnode_status_reads =
            callback.round53_mipnode_status_reads;
        out.round53_relaxation_vector_reads =
            callback.round53_relaxation_vector_reads;
        out.round53_separator_calls = callback.round53_separator_calls;
        out.round53_cut_submission_calls =
            callback.round53_cut_submission_calls;
        out.round53_callback_overhead_seconds =
            callback.cut_callback_overhead_seconds;
        if (tailored_cut_active) {
            const Round52CutManagerTelemetry& cut =
                cut_manager.telemetry();
            out.tailored_cut_callback_disabled_after_failure =
                callback.tailored_cut_disabled_after_failure;
            out.tailored_cut_callback_calls = cut.callback_calls;
            out.tailored_cut_root_callback_calls =
                cut.root_callback_calls;
            out.tailored_cut_tree_callback_calls =
                cut.tree_callback_calls;
            out.tailored_cut_nonoptimal_mipnode_callbacks =
                callback.cut_nonoptimal_mipnode_callbacks;
            out.tailored_cut_relaxation_vector_failures =
                callback.cut_relaxation_vector_failures;
            out.tailored_cuts_generated = cut.generated;
            out.tailored_cuts_violated = cut.violated;
            out.tailored_cuts_selected = cut.selected;
            out.tailored_cuts_added = cut.added;
            out.tailored_cut_duplicate_rejections =
                cut.duplicate_rejections;
            out.tailored_cut_dominated_rejections =
                cut.dominated_rejections;
            out.tailored_cut_nonviolated_rejections =
                cut.nonviolated_rejections;
            out.tailored_cut_invalid_rejections =
                cut.invalid_rejections;
            out.tailored_cut_submission_failures =
                cut.submission_failures;
            out.tailored_cut_callback_failures =
                cut.callback_failures;
            out.tailored_cut_pool_size = static_cast<long long>(
                cut.global_pool_size);
            out.tailored_cut_callback_overhead_seconds =
                callback.cut_callback_overhead_seconds;
        }
        if (!request.native_log_path.empty()) {
            // Closing the per-attempt log target makes the evidence immutable
            // before it is classified or hashed by the experiment harness.
            api_.setstrparam(model_env, GRB_STR_PAR_LOGFILE, "");
        }
        ++stats_.optimize_count;
        if (out.lp_relaxation) ++stats_.lp_relaxation_optimize_count;
        if (out.partial_bound_target_mip) {
            ++stats_.partial_bound_target_mip_optimize_count;
        }
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
        out.native_bound_target_reached = callback.bound_target_reached;
        out.round62_external_termination_requested=callback.round62_external_termination_requested;
        out.native_bound_target_termination_requested =
            callback.bound_target_termination_requested;
        if (out.partial_bound_target_mip &&
            out.native_bound_target_termination_requested &&
            out.native_status_code == GRB_INTERRUPTED) {
            // This is a mathematical state transition, not a global-deadline
            // interruption. The leaf remains open with its certified bound.
            out.interrupted = false;
        }
        if (request.capture_native_bound_events) {
            out.native_bound_events.reserve(callback.progress.events.size());
            double copied_last_bound =
                -std::numeric_limits<double>::infinity();
            for (const GurobiProgressEvent& event :
                    callback.progress.events) {
                FixedIntervalNativeBoundEvent copied;
                copied.solver_runtime_seconds =
                    event.elapsed_runtime_seconds;
                copied.work = event.work;
                copied.native_bound = event.best_bound;
                copied.native_bound_available =
                    event.best_bound_available;
                copied.native_incumbent = event.incumbent;
                copied.native_incumbent_available =
                    event.incumbent_available;
                copied.processed_nodes = event.processed_nodes;
                copied.open_nodes = event.open_nodes;
                copied.native_phase = event.phase;
                copied.bound_improved = event.best_bound_available &&
                    (!std::isfinite(copied_last_bound) ||
                     event.best_bound > copied_last_bound +
                        1e-12 * std::max(
                            1.0, std::fabs(copied_last_bound)));
                if (copied.bound_improved) {
                    copied_last_bound = event.best_bound;
                }
                copied.target_reached =
                    callback.bound_target_enabled &&
                    event.best_bound_available &&
                    event.best_bound +
                        callback.bound_target_tolerance >=
                        callback.bound_target;
                out.native_bound_events.push_back(copied);
            }
            if (out.partial_bound_target_mip) {
                stats_.native_bound_event_count +=
                    static_cast<long long>(out.native_bound_events.size());
            }
        }
        if (out.native_bound_target_reached) {
            ++stats_.native_bound_target_reached_count;
        }
        out.native_bound_available = getDouble(
            GRB_DBL_ATTR_OBJBOUNDC, out.native_bound);
        if (out.lp_relaxation && out.optimal) {
            double lp_objective = 0.0;
            if (getDouble(GRB_DBL_ATTR_OBJVAL, lp_objective)) {
                out.native_bound = lp_objective;
                out.native_bound_available = true;
                out.lp_objective_value = lp_objective;
                out.lp_objective_value_available = true;
            }
            if (request.capture_lp_primal_dual_evidence &&
                !out.lp_primal_dual_variable_evidence.empty()) {
                const int evidence_count = static_cast<int>(
                    out.lp_primal_dual_variable_evidence.size());
                std::vector<double> primal(
                    static_cast<std::size_t>(evidence_count));
                std::vector<double> reduced_cost(
                    static_cast<std::size_t>(evidence_count));
                std::vector<int> basis(
                    static_cast<std::size_t>(evidence_count));
                out.lp_primal_values_available = api_.getdblattrarray(
                    model, GRB_DBL_ATTR_X, 0, evidence_count,
                    primal.data()) == 0;
                out.lp_reduced_costs_available = api_.getdblattrarray(
                    model, GRB_DBL_ATTR_RC, 0, evidence_count,
                    reduced_cost.data()) == 0;
                out.lp_basis_status_available = api_.getintattrarray(
                    model, GRB_INT_ATTR_VBASIS, 0, evidence_count,
                    basis.data()) == 0;
                bool finite = out.lp_primal_values_available &&
                    out.lp_reduced_costs_available;
                for (int index = 0; finite && index < evidence_count;
                     ++index) {
                    auto& evidence = out.lp_primal_dual_variable_evidence[
                        static_cast<std::size_t>(index)];
                    evidence.primal_value = primal[
                        static_cast<std::size_t>(index)];
                    evidence.reduced_cost = reduced_cost[
                        static_cast<std::size_t>(index)];
                    if (out.lp_basis_status_available) {
                        evidence.variable_basis_status = basis[
                            static_cast<std::size_t>(index)];
                    }
                    finite = std::isfinite(evidence.lower_bound) &&
                        std::isfinite(evidence.upper_bound) &&
                        std::isfinite(evidence.primal_value) &&
                        std::isfinite(evidence.reduced_cost);
                }
                out.lp_primal_dual_evidence_available = finite &&
                    out.lp_basis_status_available &&
                    out.lp_objective_sense == 1 &&
                    out.model_fingerprint_matches_request;
                if (!out.lp_primal_dual_evidence_available) {
                    out.lp_primal_dual_variable_evidence.clear();
                }
            }
            if (request.capture_lp_primal_dual_evidence) {
                int constraint_count = 0;
                const bool count_ok = getInt(
                    GRB_INT_ATTR_NUMCONSTRS, constraint_count) &&
                    constraint_count >= 0;
                if (count_ok) {
                    out.lp_primal_dual_constraint_evidence.resize(
                        static_cast<std::size_t>(constraint_count));
                    std::vector<double> slacks(
                        static_cast<std::size_t>(constraint_count));
                    std::vector<double> duals(
                        static_cast<std::size_t>(constraint_count));
                    std::vector<int> basis(
                        static_cast<std::size_t>(constraint_count));
                    out.lp_constraint_slacks_available =
                        constraint_count == 0 ||
                        api_.getdblattrarray(
                            model, GRB_DBL_ATTR_SLACK, 0,
                            constraint_count, slacks.data()) == 0;
                    out.lp_constraint_duals_available =
                        constraint_count == 0 ||
                        api_.getdblattrarray(
                            model, GRB_DBL_ATTR_PI, 0,
                            constraint_count, duals.data()) == 0;
                    out.lp_constraint_basis_status_available =
                        constraint_count == 0 ||
                        api_.getintattrarray(
                            model, GRB_INT_ATTR_CBASIS, 0,
                            constraint_count, basis.data()) == 0;
                    bool constraint_metadata_ok =
                        out.lp_constraint_slacks_available &&
                        out.lp_constraint_duals_available &&
                        out.lp_constraint_basis_status_available;
                    for (int index = 0;
                         constraint_metadata_ok &&
                         index < constraint_count; ++index) {
                        char* name = nullptr;
                        constraint_metadata_ok =
                            api_.getstrattrelement(
                                model, GRB_STR_ATTR_CONSTRNAME,
                                index, &name) == 0 && name && *name &&
                            std::isfinite(slacks[
                                static_cast<std::size_t>(index)]) &&
                            std::isfinite(duals[
                                static_cast<std::size_t>(index)]);
                        if (constraint_metadata_ok) {
                            auto& evidence =
                                out.lp_primal_dual_constraint_evidence[
                                    static_cast<std::size_t>(index)];
                            evidence.name = name;
                            evidence.slack = slacks[
                                static_cast<std::size_t>(index)];
                            evidence.dual_multiplier = duals[
                                static_cast<std::size_t>(index)];
                            evidence.constraint_basis_status = basis[
                                static_cast<std::size_t>(index)];
                        }
                    }
                    out.lp_constraint_evidence_available =
                        constraint_metadata_ok &&
                        out.model_fingerprint_matches_request;
                    if (!out.lp_constraint_evidence_available) {
                        out.lp_primal_dual_constraint_evidence.clear();
                    }
                }
            }
            int diagnostic_variables = 0;
            if (getInt(GRB_INT_ATTR_NUMVARS, diagnostic_variables) &&
                diagnostic_variables > 0) {
                std::vector<double> solution(
                    static_cast<std::size_t>(diagnostic_variables));
                std::unordered_map<std::string, double> values;
                bool diagnostics_ok = api_.getdblattrarray(
                    model, GRB_DBL_ATTR_X, 0, diagnostic_variables,
                    solution.data()) == 0;
                for (int index = 0; diagnostics_ok &&
                     index < diagnostic_variables; ++index) {
                    char* name = nullptr;
                    diagnostics_ok = api_.getstrattrelement(
                        model, GRB_STR_ATTR_VARNAME, index, &name) == 0 &&
                        name && *name;
                    if (diagnostics_ok) {
                        values[name] = solution[
                            static_cast<std::size_t>(index)];
                    }
                }
                auto fractionality = [](double value) {
                    const double clipped = std::max(
                        0.0, std::min(1.0, value));
                    return 4.0 * clipped * (1.0 - clipped);
                };
                if (diagnostics_ok) {
                    for (const auto& item : values) {
                        if (item.first.rfind("x_", 0) == 0) {
                            out.route_binary_fractionality +=
                                fractionality(item.second);
                        } else if (item.first.rfind("z_", 0) == 0) {
                            out.visit_binary_fractionality +=
                                fractionality(item.second);
                        } else if (item.first.rfind("bit_", 0) == 0) {
                            out.inventory_bit_fractionality +=
                                fractionality(item.second);
                        } else if (item.first.rfind("seg_z_", 0) == 0) {
                            out.selector_binary_fractionality +=
                                fractionality(item.second);
                        }
                    }
                    const auto global_g = values.find("G");
                    if (global_g != values.end()) {
                        out.lp_g_value = global_g->second;
                        out.lp_g_value_available =
                            std::isfinite(out.lp_g_value);
                        for (const auto& item : values) {
                            if (item.first.rfind("bit_", 0) != 0) continue;
                            const double bit = item.second;
                            const double lower = request.gamma_L;
                            const double upper = request.gamma_U;
                            const double mc_lower = std::max(
                                lower * bit,
                                global_g->second - upper * (1.0 - bit));
                            const double mc_upper = std::min(
                                upper * bit,
                                global_g->second - lower * (1.0 - bit));
                            out.mccormick_ambiguity +=
                                std::max(0.0, mc_upper - mc_lower);
                        }
                    }
                    const std::regex activation_pattern(
                        R"(^seg_w_([0-9]+)_([0-9]+)_([0-9]+)$)");
                    for (const auto& item : values) {
                        std::smatch match;
                        if (!std::regex_match(
                                item.first, match, activation_pattern)) {
                            continue;
                        }
                        const std::string i = match[1].str();
                        const std::string b = match[2].str();
                        const int segment = std::stoi(match[3].str());
                        const std::string selected_g_name =
                            "seg_G_" + std::to_string(segment);
                        const std::string selector_name =
                            "seg_z_" + std::to_string(segment);
                        const std::string product_name =
                            "seg_q_" + i + "_" + b + "_" +
                            std::to_string(segment);
                        const auto selected_g = values.find(selected_g_name);
                        const auto selector = values.find(selector_name);
                        const auto product = values.find(product_name);
                        if (selected_g == values.end() ||
                            selector == values.end() ||
                            product == values.end()) {
                            diagnostics_ok = false;
                            break;
                        }
                        const double midpoint = request.gamma_L + 0.5 *
                            (request.gamma_U - request.gamma_L);
                        const double lower = segment == 0
                            ? request.gamma_L : midpoint;
                        const double upper = segment == 0
                            ? midpoint : request.gamma_U;
                        const double activation = item.second;
                        const double inactive =
                            selector->second - activation;
                        const double mc_lower = std::max(
                            lower * activation,
                            selected_g->second - upper * inactive);
                        const double mc_upper = std::min(
                            upper * activation,
                            selected_g->second - lower * inactive);
                        out.segmented_mccormick_ambiguity +=
                            std::max(0.0, mc_upper - mc_lower);
                    }
                }
                out.lp_solution_diagnostics_available = diagnostics_ok;
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
        if (out.partial_bound_target_mip) {
            stats_.cumulative_partial_bound_target_mip_work += out.work;
        }
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
        if (request.round62_external_stop) {
            out.round62_numeric_valid=out.native_status_code==GRB_OPTIMAL ||
                out.native_status_code==GRB_INTERRUPTED || out.native_status_code==GRB_TIME_LIMIT ||
                out.native_status_code==GRB_INFEASIBLE;
            if (solution_count>0) {
                for (const char* attr:{"ConstrVio","BoundVio","IntVio"}) {
                    double violation=0;
                    out.round62_numeric_valid=out.round62_numeric_valid &&
                        getDouble(attr,violation) && violation<=1e-5;
                }
            }
            std::ifstream quality_log(request.native_log_path);
            std::string quality_line;
            while(std::getline(quality_log,quality_line)) {
                std::transform(quality_line.begin(),quality_line.end(),quality_line.begin(),
                    [](unsigned char c){return static_cast<char>(std::tolower(c));});
                if(quality_line.find("numerical trouble")!=std::string::npos ||
                   quality_line.find("unscaled primal violation")!=std::string::npos ||
                   quality_line.find("unscaled dual violation")!=std::string::npos)
                    out.round62_numeric_valid=false;
            }
        }
        out.presolved_model_size_available =
            log_evidence.presolved_size_available;
        out.presolved_row_count = log_evidence.presolved_rows;
        out.presolved_column_count = log_evidence.presolved_columns;
        out.presolved_nonzero_count = log_evidence.presolved_nonzeros;
        out.root_relaxation_bound_available =
            log_evidence.root_relaxation_bound_available;
        out.root_relaxation_bound = log_evidence.root_relaxation_bound;
        out.root_runtime_seconds = log_evidence.root_runtime_seconds;
        out.root_simplex_iterations =
            log_evidence.root_simplex_iterations;
        out.root_cut_family_evidence = log_evidence.root_cut_families;
        long long root_cut_total = 0;
        for (const auto& cut : out.root_cut_family_evidence) {
            root_cut_total += cut.count;
        }
        out.native_cut_count_available = !out.root_cut_family_evidence.empty();
        out.native_cut_count = root_cut_total;
        for (const FixedIntervalNativeBoundEvent& event :
             out.native_bound_events) {
            if (out.first_incumbent_runtime_seconds < 0.0 &&
                event.native_incumbent_available) {
                out.first_incumbent_runtime_seconds =
                    event.solver_runtime_seconds;
                out.first_incumbent_work = event.work;
            }
            if (event.processed_nodes <= 0.0 &&
                event.native_bound_available) {
                out.final_root_cut_bound_available = true;
                out.final_root_cut_bound = event.native_bound;
                out.root_work = std::max(out.root_work, event.work);
                out.root_runtime_seconds = std::max(
                    out.root_runtime_seconds,
                    event.solver_runtime_seconds);
            }
        }
        if (!out.final_root_cut_bound_available &&
            out.root_relaxation_bound_available) {
            out.final_root_cut_bound_available = true;
            out.final_root_cut_bound = out.root_relaxation_bound;
        }
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
    result.gurobi_hga_start_requested = options.gurobi_hga_start;
    result.gurobi_mip_gap_requested = 0.0;
    result.gurobi_mip_gap_abs_requested = 0.0;
    result.solver_thread_policy = "plain_gurobi_single_thread";
    result.thread_fairness_class = "one_thread_fair";
    result.strict_certificate_policy_version =
        "round24-gurobi-engineering-exact-v1";

    try {
        HgaTgbcResult hga_seed;
        if (options.gurobi_hga_start) {
            recordProcessPhase(
                options, "plain_gurobi_hga_start", "start",
                "independently_verified_same_hga_incumbent_ablation");
            HgaTgbcOptions hga_options;
            hga_options.lambda = options.lambda;
            hga_options.seed = options.primal_heuristic_seed;
            hga_options.stop_mode = options.primal_heuristic_stop;
            hga_options.no_improve_generation_limit =
                options.primal_heuristic_no_improve_generations;
            hga_options.generation_log_path =
                options.primal_heuristic_generation_log;
            hga_options.phase_label = "p_grb_hga_ablation";
            hga_options.process_options = &options;
            hga_options.max_time_seconds = std::max(
                1, static_cast<int>(
                    std::ceil(options.primal_heuristic_seconds)));
            hga_options.pop_size =
                std::max(24, options.primal_heuristic_runs);
            hga_seed = runHgaTgbcNative(instance, hga_options);
            result.gurobi_hga_incumbent_found = hga_seed.found;
            result.gurobi_hga_verified_objective =
                hga_seed.verified_objective;
            result.gurobi_hga_runtime_seconds =
                hga_seed.wall_time_seconds;
            result.primal_heuristic = "hga-tgbc";
            result.hga_total_generations = hga_seed.total_generations;
            result.hga_generations_since_improvement =
                hga_seed.generations_since_improvement;
            result.hga_generation_log_path =
                hga_seed.generation_log_path.string();
            result.incumbent_generation_time_seconds =
                hga_seed.wall_time_seconds;
            result.incumbent_generation_method =
                "round31_p_grb_hga_ablation";
            recordProcessPhase(
                options, "plain_gurobi_hga_complete",
                hga_seed.found ? "complete" : "failed",
                hga_seed.found
                    ? "independently_verified_hga_incumbent_available"
                    : "no_verified_hga_incumbent");
        }
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

        // P-GRB is unconditionally plain and never consults a Tailored seed
        // or strengthened-model switch. Round 31's explicitly named
        // P-GRB-HGA diagnostic may submit the separately verified HGA start;
        // it changes no model row, bound, parameter, or benchmark role.
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
        std::vector<std::string> native_names(native_lb.size());
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
            native_names[static_cast<std::size_t>(index)] = name;
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

        if (options.gurobi_hga_start) {
            if (!hga_seed.found || !native_arrays_ok) {
                result.gurobi_hga_start_status = !hga_seed.found
                    ? "no_independently_verified_hga_incumbent"
                    : "native_model_domain_unavailable";
            } else {
                SolverNeutralModelDomain domain;
                domain.names = native_names;
                domain.lower_bounds = native_lb;
                domain.upper_bounds = native_ub;
                domain.variable_types = native_type;
                std::vector<RoutePlan> nonempty_routes;
                for (const RoutePlan& route : hga_seed.routes) {
                    if (route.nodes.size() == 2 &&
                        route.nodes.front() == 0 &&
                        route.nodes.back() == 0 &&
                        route.operations.empty()) {
                        continue;
                    }
                    nonempty_routes.push_back(route);
                }
                const SolverNeutralMipStart mapped =
                    mapVerifiedRoutesToCanonicalModel(
                        instance, options, nonempty_routes,
                        "round31_p_grb_hga_ablation", 0.0, 1.0,
                        hga_seed.verified_objective, domain);
                result.gurobi_hga_start_mapping_complete =
                    mapped.complete;
                if (mapped.complete) {
                    result.gurobi_hga_start_return_code =
                        api.setdblattrarray(
                            model, GRB_DBL_ATTR_START, 0,
                            result.gurobi_num_vars,
                            const_cast<double*>(mapped.values.data()));
                    result.gurobi_hga_start_submitted =
                        result.gurobi_hga_start_return_code == 0;
                    result.gurobi_hga_start_status =
                        result.gurobi_hga_start_submitted
                            ? "submitted_complete_independently_verified_start"
                            : "native_start_submission_failed";
                } else {
                    result.gurobi_hga_start_status =
                        "mapping_rejected:" + mapped.failure_reason;
                }
            }
        }

        ProgressCallbackState callback;
        callback.api = &api;
        const int callback_rc = api.setcallbackfunc(
            model, progressAndBoundTargetCallback, &callback);
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
