#include "GurobiProgress.hpp"

#include <fstream>
#include <iomanip>

namespace ebrp {

bool writeGurobiProgressCsv(const std::filesystem::path& path,
                            const GurobiProgressStats& progress,
                            std::string* reason) {
    try {
        if (path.empty()) {
            if (reason) *reason = "empty_progress_path";
            return false;
        }
        if (path.has_parent_path()) {
            std::filesystem::create_directories(path.parent_path());
        }
        std::ofstream out(path, std::ios::out | std::ios::trunc);
        if (!out) {
            if (reason) *reason = "cannot_open_progress_path";
            return false;
        }
        out << "event_sequence,elapsed_runtime_seconds,work,incumbent_available,"
               "incumbent,best_bound_available,best_bound,processed_nodes,"
               "open_nodes,solution_count,callback_where,phase,context\n";
        out << std::setprecision(17);
        for (std::size_t index = 0; index < progress.events.size(); ++index) {
            const GurobiProgressEvent& event = progress.events[index];
            out << index << ',' << event.elapsed_runtime_seconds << ','
                << event.work << ','
                << (event.incumbent_available ? "true" : "false") << ','
                << event.incumbent << ','
                << (event.best_bound_available ? "true" : "false") << ','
                << event.best_bound << ',' << event.processed_nodes << ','
                << event.open_nodes << ',' << event.solution_count << ','
                << event.callback_where << ',' << event.phase << ','
                << event.context << '\n';
        }
        if (!out) {
            if (reason) *reason = "progress_write_failed";
            return false;
        }
        if (reason) *reason = "written";
        return true;
    } catch (const std::exception& ex) {
        if (reason) *reason = ex.what();
        return false;
    }
}

} // namespace ebrp
