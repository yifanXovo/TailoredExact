#pragma once

#include "Instance.hpp"

#include <string>
#include <vector>

namespace ebrp {

bool isPaperK1AmSfPresetOrAlias(const std::string& lower_name);

// Apply the complete uniform override layer that historically followed the
// paper-gf-tailored-bc preset in the Round 52/53 K1-AM commands.
void configurePaperK1AmSfOverrides(SolveOptions& options);

const std::vector<std::string>& paperK1AmSfActiveFamilies();
const std::vector<std::string>& paperK1AmSfInactiveFamilies();

} // namespace ebrp
