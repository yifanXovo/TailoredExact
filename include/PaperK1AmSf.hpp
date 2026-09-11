#pragma once

#include "Instance.hpp"

#include <string>
#include <vector>

namespace ebrp {

bool isPaperK1AmSfPresetOrAlias(const std::string& lower_name);

// Single authoritative construction contract for the canonical K1 fixed
// interval model. It contains model flags only, so build-only and full
// controller entry points can share the same effective F0 identity.
void configurePaperK1AmSfCanonicalF0(SolveOptions& options);

// Apply the complete uniform override layer that historically followed the
// paper-gf-tailored-bc preset in the Round 52/53 K1-AM commands.
void configurePaperK1AmSfOverrides(SolveOptions& options);

const std::vector<std::string>& paperK1AmSfActiveFamilies();
const std::vector<std::string>& paperK1AmSfInactiveFamilies();

} // namespace ebrp
