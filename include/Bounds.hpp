#pragma once

#include "Instance.hpp"

#include <limits>
#include <string>

namespace ebrp {

struct ResourceRelaxationBound {
    bool computed = false;
    int total_pickup_limit = 0;
    long long states_processed = 0;
    double penalty_lower_bound = 0.0;
    double objective_lower_bound = 0.0;
    std::string note;
};

struct GiniIntervalInventoryRelaxationBound {
    bool computed = false;
    bool infeasible = false;
    int total_pickup_limit = 0;
    double objective_lower_bound = 0.0;
    double gini_lower_bound = 0.0;
    double lambda_penalty_lower_bound = 0.0;
    std::string status;
    std::string note;
};

ResourceRelaxationBound computeResourceRelaxationBound(const Instance& instance,
                                                       double lambda);

GiniIntervalInventoryRelaxationBound computeGiniIntervalInventoryRelaxationBound(
    const Instance& instance,
    double lambda,
    double gamma_floor,
    double gamma_cap,
    double time_limit_seconds = 5.0,
    double objective_cutoff = std::numeric_limits<double>::infinity(),
    int route_mask_max_v = 12);

} // namespace ebrp
