#pragma once

#include "StationSet.hpp"

#include <string>
#include <vector>

namespace ebrp {

struct RouteLoadColumn {
    int vehicle = 0;
    int mask = 0;
    StationSet station_set;      // dynamic station membership for V > 63 / large diagnostics
    std::vector<int> path;      // station sequence, depot omitted
    std::vector<int> q;         // index 1..V; pickup positive, drop negative
    int pickup = 0;
    double travel = 0.0;
    double duration = 0.0;
    double reduced_cost = 0.0;
    std::string column_kind = "elementary_feasible";
    bool elementary = true;
    std::string relaxation_scope = "original_elementary";
    bool can_be_used_for_incumbent = true;
    bool can_be_used_for_lower_bound = true;
    bool has_repeated_stations = false;
    int repeated_station_count = 0;
};

} // namespace ebrp
