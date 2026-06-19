#include "Logger.hpp"

#include <chrono>
#include <filesystem>
#include <iomanip>

namespace ebrp {

Logger::Logger(const std::string& path) {
    open(path);
}

void Logger::open(const std::string& path) {
    if (path.empty()) return;
    std::filesystem::path p(path);
    if (p.has_parent_path()) std::filesystem::create_directories(p.parent_path());
    out_.open(path);
}

void Logger::line(const std::string& text) {
    if (!out_) return;
    out_ << text << '\n';
}

bool Logger::enabled() const {
    return static_cast<bool>(out_);
}

} // namespace ebrp
