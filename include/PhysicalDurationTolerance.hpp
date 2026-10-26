#pragma once

namespace ebrp {

// The existing Evaluator duration acceptance tolerance. The Round92 proof
// refers to this exact binary64 object; changing it changes both contracts.
inline constexpr double kPhysicalDurationTolerance = 1e-7;

} // namespace ebrp
