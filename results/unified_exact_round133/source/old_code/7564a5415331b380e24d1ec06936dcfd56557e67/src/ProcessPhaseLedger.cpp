#include "ProcessPhaseLedger.hpp"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>

namespace ebrp {
namespace {

std::atomic<long long> sequence{0};

std::string csv(const std::string& value) {
    std::string out;
    out.reserve(value.size() + 2);
    out.push_back('"');
    for (const char ch : value) {
        if (ch == '"') out.push_back('"');
        out.push_back(ch);
    }
    out.push_back('"');
    return out;
}

double nominalBudget(const SolveOptions& options) {
    return options.process_wall_time_limit > 0.0
        ? options.process_wall_time_limit
        : options.solve_time_limit;
}

} // namespace

double processElapsedSeconds(const SolveOptions& options) {
    if (!options.process_start_time_valid) return 0.0;
    return std::max(0.0, std::chrono::duration<double>(
        std::chrono::steady_clock::now() - options.process_start_time).count());
}

bool processDeadlineConfigured(const SolveOptions& options) {
    return options.process_start_time_valid && nominalBudget(options) > 0.0;
}

double processDeadlineRemainingSeconds(const SolveOptions& options) {
    if (!processDeadlineConfigured(options)) {
        return std::numeric_limits<double>::max();
    }
    return nominalBudget(options) - processElapsedSeconds(options);
}

double processWorkRemainingSeconds(const SolveOptions& options) {
    const double remaining = processDeadlineRemainingSeconds(options);
    if (!std::isfinite(remaining)) return remaining;
    return remaining - std::max(0.0, options.process_shutdown_margin_seconds);
}

bool processWorkDeadlineReached(const SolveOptions& options) {
    return processDeadlineConfigured(options) &&
        processWorkRemainingSeconds(options) <= 0.0;
}

void recordProcessPhase(const SolveOptions& options,
                        const std::string& event,
                        const std::string& status,
                        const std::string& detail) {
    if (options.process_phase_ledger_path.empty()) return;
    const std::filesystem::path path(options.process_phase_ledger_path);
    if (path.has_parent_path()) {
        std::filesystem::create_directories(path.parent_path());
    }
    const bool header = !std::filesystem::exists(path) ||
        std::filesystem::file_size(path) == 0;
    std::ofstream out(path, std::ios::out | std::ios::app);
    if (!out) return;
    if (header) {
        out << "sequence,process_seconds,event,status,"
               "nominal_deadline_remaining_seconds,"
               "work_deadline_remaining_seconds,detail\n";
    }
    const double nominal = processDeadlineRemainingSeconds(options);
    const double work = processWorkRemainingSeconds(options);
    const double event_time =
        event == "process_entry" ? 0.0 : processElapsedSeconds(options);
    out << sequence.fetch_add(1) << ',' << std::setprecision(17)
        << event_time << ',' << csv(event) << ','
        << csv(status) << ',';
    if (std::isfinite(nominal)) out << nominal;
    out << ',';
    if (std::isfinite(work)) out << work;
    out << ',' << csv(detail) << '\n';
    out.flush();
}

} // namespace ebrp
