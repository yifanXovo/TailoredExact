#pragma once
#include "Result.hpp"
#include <filesystem>
#include <functional>

namespace ebrp::round160 {
// Opt-in primal interface. This component never supplies a global lower bound.
struct Config {
    int block_size=8, extra_ports=8, nodes=512, passes=1;
    bool fixed_old_owner=false, uncompressed=false, qualify_only=false;
    std::vector<int> block;
};
struct Outcome {
    std::vector<RoutePlan> routes;
    double objective=0.;
    int calls=0, improvements=0, anchors=0;
    bool deadline=false;
};
Outcome optimize(const Instance&, double lambda, const std::vector<RoutePlan>& parent,
                 const std::filesystem::path& evidence, const Config&,
                 const std::function<double()>& remaining);
// Explicit command-line switch; default false for every production entry.
bool& enabled();
}
