#pragma once

#include <filesystem>
#include <string>

namespace ebrp {
std::string fileSha256(const std::filesystem::path& path);
} // namespace ebrp
