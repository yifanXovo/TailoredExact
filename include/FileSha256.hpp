#pragma once

#include <filesystem>
#include <string>

namespace ebrp {
std::string textSha256(const std::string& text);
std::string fileSha256(const std::filesystem::path& path);
} // namespace ebrp
