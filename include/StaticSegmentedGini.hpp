#pragma once

#include "GiniFrontierGeometry.hpp"

#include <string>
#include <vector>

namespace ebrp {

struct Round41StaticK2Geometry {
    bool valid = false;
    double proof_lower = 0.0;
    double proof_upper = 0.0;
    double midpoint = 0.0;
    std::vector<GiniIntervalGeometry> segments;
    std::string reason = "not_evaluated";
};

Round41StaticK2Geometry makeRound41StaticK2Geometry(
    double proof_lower,
    double proof_upper,
    double tolerance);

// Returns whether (z, b, G, Gk, w, q) satisfies the complete linear
// perspective block used for one segment and q = G*b at integral z,b.
bool round41PerspectiveProductBlockValid(
    double segment_lower,
    double segment_upper,
    double selector,
    double bit,
    double global_g,
    double segment_g,
    double activation,
    double product,
    double tolerance,
    std::string* reason = nullptr);

// Safe scalar binary-product block y = z*x for x in [global_lower,
// global_upper], with selected-domain tightening y in
// [selected_lower*z,selected_upper*z].
bool round41SelectedContinuousBlockValid(
    double global_lower,
    double global_upper,
    double selected_lower,
    double selected_upper,
    double selector,
    double original,
    double selected,
    double tolerance,
    std::string* reason = nullptr);

} // namespace ebrp
