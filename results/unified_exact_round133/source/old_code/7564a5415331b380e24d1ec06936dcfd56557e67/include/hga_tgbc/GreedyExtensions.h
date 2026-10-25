#pragma once
#include "Solvers.h"
#include <vector>

struct GreedyRouteProfile {
    double objective_value = 0.0;            // same sign convention as nGreedyLU_RA_route_incremental: larger is better
    std::vector<int> visited_nodes;          // 1-based, truncated/effective route used by greedy
    std::vector<int> visit_oper;             // per visited node; positive=pickup, negative=drop
    std::vector<int> load_after_visit;       // cumulative vehicle load after each visited node
    int pickup_budget = 0;
    int pickups_used = 0;
    double travel_time = 0.0;
};

struct GreedyCompactionInfo {
    bool had_zero_op_prefix = false;
    std::vector<std::vector<int>> compacted_routes;
    SolutionResult_ORO first_pass_result;
    SolutionResult_ORO rerun_result;
};

SolutionResult_ORO nGreedyLU_RA_route_incremental_norm(int V, double total_time_limit,
    const std::vector<int>& route, int Q_single,
    const std::vector<int>& s0, const std::vector<int>& c0, const std::vector<int>& t0,
    const std::vector<std::vector<double>>& dist,
    const std::vector<int>& fixed_station_oper0,
    const std::vector<double>& W0, const std::vector<double>& min_ratio0,
    double lambda, double scaling);

GreedyRouteProfile nGreedyLU_RA_route_profile_incremental(int V, double total_time_limit,
    const std::vector<int>& route, int Q_single,
    const std::vector<int>& s, const std::vector<int>& c, const std::vector<int>& t,
    const std::vector<std::vector<double>>& dist,
    const std::vector<int>& fixed_station_oper,
    const std::vector<double>& Wi, const std::vector<double>& min_ratio,
    double lambda, double scaling);

GreedyRouteProfile nGreedyLU_RA_route_profile_incremental_norm(int V, double total_time_limit,
    const std::vector<int>& route, int Q_single,
    const std::vector<int>& s0, const std::vector<int>& c0, const std::vector<int>& t0,
    const std::vector<std::vector<double>>& dist,
    const std::vector<int>& fixed_station_oper0,
    const std::vector<double>& W0, const std::vector<double>& min_ratio0,
    double lambda, double scaling);

SolutionResult_ORO nGreedyLU_RA_compact_full(int IterNum, int V, int M, double total_time_limit,
    const std::vector<std::vector<int>>& routes, const std::vector<int>& Q,
    const std::vector<int>& s, const std::vector<int>& c, const std::vector<int>& t,
    const std::vector<std::vector<double>>& dist, const int& max_iter, const double& r_avg_start,
    const std::vector<double>& W, const std::vector<double>& min_ratio,
    double lambda, double scaling, GreedyCompactionInfo* info = nullptr);

SolutionResult_ORO nGreedyLU_RA_compact_incremental(int IterNum, int V, int M, double total_time_limit,
    const std::vector<std::vector<int>>& routes, const std::vector<int>& Q,
    const std::vector<int>& s, const std::vector<int>& c, const std::vector<int>& t,
    const std::vector<std::vector<double>>& dist, const int& max_iter, const double& r_avg_start,
    const std::vector<double>& W, const std::vector<double>& min_ratio,
    double lambda, double scaling, GreedyCompactionInfo* info = nullptr);
