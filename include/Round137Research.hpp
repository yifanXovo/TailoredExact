#pragma once
#include "Instance.hpp"
#include <cmath>
#include <stdexcept>

namespace ebrp {
// Explicit research controls. The ordinary ms2 formulation and compatibility
// defaults are unchanged. No instance, size, Seed or elapsed-time dispatch.
struct Round137Controls {
    bool delete_ab = false;
    bool delete_cr = false;
    bool delete_cg = false;
    double am_threshold = -1.0;
    bool am_threshold_explicit = false;
};
inline Round137Controls& round137() { static Round137Controls c; return c; }
inline bool round137EmitAB() { return !round137().delete_ab; }
inline void round137Apply(SolveOptions& opt, const std::string& mode) {
    const auto& c = round137();
    const int deletions = int(c.delete_ab) + int(c.delete_cr) + int(c.delete_cg);
    if ((deletions || c.am_threshold_explicit) && mode != "ms2")
        throw std::runtime_error("Round137 research controls require ms2");
    if (deletions > 1 || (deletions && c.am_threshold_explicit))
        throw std::runtime_error("Round137 permits one declared change per comparison");
    if (c.am_threshold_explicit) {
        if (!std::isfinite(c.am_threshold) || c.am_threshold < 0 || c.am_threshold > 1)
            throw std::runtime_error("Round137 AM threshold must be in [0,1]");
        // Called after all presets: this is the first-class controller field.
        opt.split_threshold = c.am_threshold;
    }
}
}
