#pragma once

#include "Instance.hpp"

#include <filesystem>
#include <vector>

namespace ebrp {

Instance parseInstanceFile(const std::filesystem::path& path,
                           double total_time_limit,
                           double pickup_time,
                           double drop_time);

std::vector<std::filesystem::path> collectInputFiles(const std::filesystem::path& input);

} // namespace ebrp
