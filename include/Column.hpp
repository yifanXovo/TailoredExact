#pragma once

#include <vector>

namespace ebrp {

struct RouteLoadColumn {
    int vehicle = 0;
    int mask = 0;
    std::vector<int> path;      // station sequence, depot omitted
    std::vector<int> q;         // index 1..V; pickup positive, drop negative
    int pickup = 0;
    double travel = 0.0;
    double duration = 0.0;
    double reduced_cost = 0.0;
};

} // namespace ebrp
