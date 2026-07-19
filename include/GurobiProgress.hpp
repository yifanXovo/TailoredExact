#pragma once

#include <filesystem>
#include <string>
#include <vector>

namespace ebrp {

struct GurobiProgressEvent {
    double elapsed_runtime_seconds = 0.0;
    double work = 0.0;
    double incumbent = 0.0;
    bool incumbent_available = false;
    double best_bound = 0.0;
    bool best_bound_available = false;
    double processed_nodes = 0.0;
    double open_nodes = 0.0;
    double solution_count = 0.0;
    int callback_where = 0;
    int phase = -1;
    std::string context;
};

struct GurobiProgressStats {
    long long callback_invocations = 0;
    long long records = 0;
    long long dropped_records = 0;
    double first_incumbent_time = -1.0;
    double last_lower_bound_improvement_time = -1.0;
    bool read_only_contract = true;
    bool deadline_termination_used = false;
    std::vector<GurobiProgressEvent> events;
};

bool writeGurobiProgressCsv(const std::filesystem::path& path,
                            const GurobiProgressStats& progress,
                            std::string* reason = nullptr);

} // namespace ebrp
