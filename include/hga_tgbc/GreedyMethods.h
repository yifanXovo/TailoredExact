#pragma once
#include "Solvers.h"
#include "AVLCalculator.h"
#include "GreedyExtensions.h"
#include <vector>

double GreedyLU_RA(int IterNum, int V, int M, double total_time_limit, const std::vector<std::vector<int>>& routes, const std::vector<int>& Q,
    const std::vector<int>& s, const std::vector<int>& c, const std::vector<int>& t, const std::vector<std::vector<double>>& dist);

double Greedy_LU(int V, int M, const std::vector<std::vector<int>>& routes, const std::vector<int>& Q_list,
    const std::vector<int>& s, const std::vector<int>& c, const std::vector<int>& t);

void set_greedy_time_units(double load_unit, double unload_unit);
void set_greedy_time_units_cut(double load_unit, double unload_unit);
void set_greedy_objective_params(double lambda, double scaling);
void set_greedy_route_stats(bool enabled);
double get_greedy_objective_lambda();
double get_greedy_objective_scaling();

SolutionResult_ORO nF_R(int IterNum, int V, int M, double r_avgi, double total_time_limit, const std::vector<std::vector<int>>& routes, const std::vector<int>& Q,
    const std::vector<std::vector<double>>& dist, const std::vector<int>& Y_Ii, const std::vector<int>& Y_Ri, const std::vector<int>& Ci,
    const std::vector<double>& W = std::vector<double>(), const std::vector<double>& min_ratio = std::vector<double>(),
    double lambda = 0.15, double scaling = 1.0);

SolutionResult_ORO nGreedyLU_RA(int IterNum, int V, int M, double total_time_limit, const std::vector<std::vector<int>>& routes, const std::vector<int>& Q,
    const std::vector<int>& s, const std::vector<int>& c, const std::vector<int>& t, const std::vector<std::vector<double>>& dist,
    const int& max_iter, const double& r_avg_start, const std::vector<double>& W = std::vector<double>(),
    const std::vector<double>& min_ratio = std::vector<double>(), double lambda = 0.15, double scaling = 1.0);

SolutionResult_ORO nGreedyLU_RA_route_incremental(int V, double total_time_limit,
    const std::vector<int>& route, int Q_single,
    const std::vector<int>& s, const std::vector<int>& c, const std::vector<int>& t,
    const std::vector<std::vector<double>>& dist,
    const std::vector<int>& fixed_station_oper,
    const std::vector<double>& W,
    const std::vector<double>& min_ratio,
    double lambda, double scaling);

SolutionResult_ORO nGreedyLU_RA_compact_full(int IterNum, int V, int M, double total_time_limit,
    const std::vector<std::vector<int>>& routes, const std::vector<int>& Q,
    const std::vector<int>& s, const std::vector<int>& c, const std::vector<int>& t,
    const std::vector<std::vector<double>>& dist, const int& max_iter,
    const double& r_avg_start, const std::vector<double>& W,
    const std::vector<double>& min_ratio, double lambda, double scaling,
    GreedyCompactionInfo* info);

SolutionResult_ORO nGreedyLU_RA_compact_incremental(int IterNum, int V, int M, double total_time_limit,
    const std::vector<std::vector<int>>& routes, const std::vector<int>& Q,
    const std::vector<int>& s, const std::vector<int>& c, const std::vector<int>& t,
    const std::vector<std::vector<double>>& dist, const int& max_iter,
    const double& r_avg_start, const std::vector<double>& W,
    const std::vector<double>& min_ratio, double lambda, double scaling,
    GreedyCompactionInfo* info);

SolutionResult_ORO nGreedyLU_RA_cut(int IterNum, int V, int M, double total_time_limit, const std::vector<std::vector<int>>& routes, const std::vector<int>& Q,
    const std::vector<int>& s, const std::vector<int>& c, const std::vector<int>& t, const std::vector<std::vector<double>>& dist,
    const int& max_iter, const double& r_avg_start, const std::vector<double>& W = std::vector<double>(),
    const std::vector<double>& min_ratio = std::vector<double>(), double lambda = 0.15, double scaling = 1.0);
