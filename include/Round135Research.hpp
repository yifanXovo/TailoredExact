#pragma once

#include "Round127Research.hpp"
#include <cmath>
#include <stdexcept>

namespace ebrp {
// Explicit, process-local research control. No SolveOptions/archive ABI change.
inline bool& round135AggregatePenalty() { static bool enabled = false; return enabled; }
inline void round135Validate() {
    if (round135AggregatePenalty() && round127().mode != "ms2" &&
        round127().mode != "s2-root")
        throw std::runtime_error("Round135 AP requires the unchanged S2 method");
}

// c and weight are the actual binary64 coefficients. fma rounds c*y-1
// only once; moving its absolute value toward zero gives a lower bound
// on |c*y-1|. The second downward step protects the weighted product.
// This is done once per legal state while constructing a model, never at nodes.
inline double round135PenaltyCoefficient(double c, int y, double weight) {
    if (!(std::isfinite(c) && c > 0 && y >= 0 &&
          std::isfinite(weight) && weight >= 0))
        throw std::runtime_error("Invalid Round135 AP state coefficient");
    if (weight == 0) return 0;
    const double deviation = std::fabs(std::fma(c, static_cast<double>(y), -1.0));
    if (!std::isfinite(deviation))
        throw std::runtime_error("Nonfinite Round135 AP deviation");
    const double lower = deviation > 0 ? std::nextafter(deviation, 0.0) : 0.0;
    const double weighted = weight * lower;
    if (!std::isfinite(weighted))
        throw std::runtime_error("Nonfinite Round135 AP weighted coefficient");
    return weighted > 0 ? std::nextafter(weighted, 0.0) : 0.0;
}
} // namespace ebrp
