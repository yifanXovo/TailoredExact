#pragma once

#include <fstream>
#include <string>

namespace ebrp {

class Logger {
public:
    Logger() = default;
    explicit Logger(const std::string& path);
    void open(const std::string& path);
    void line(const std::string& text);
    bool enabled() const;

private:
    std::ofstream out_;
};

} // namespace ebrp
