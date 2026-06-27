#pragma once

#include <vector>
#include <random>
#include <algorithm>
#include <tuple>

struct SolutionResult_T1 {
    double objective_value;
    std::vector<std::vector<int>> routes;
    std::vector<std::tuple<int, int, int, int>> operations;
    double lower_bound = 0.0;
    double upper_bound = 0.0;
    double gini_value = 0.0;
    double weighted_avg = 0.0;
};

struct SolutionResult_T2 {
    double objective_value;
    std::vector<double> p_values;
    std::vector<double> r_values;
    int total_service_time;
};

struct SolutionResult_ORO {
    double objective_value;
    double r_avg_best;
    std::vector<int> Y_Oper_best;
};

void set_solver_objective_params(double lambda, double scaling);
double get_solver_objective_lambda();
double get_solver_objective_scaling();

SolutionResult_T1 Solver_CPLEX(
    int V,
    int M,
    int Q,
	double total_time_limit,
    std::vector<int> C,
    std::vector<int> Y_I,
    std::vector<int> Y_R,
    const std::vector<std::vector<double>>& dist,
    const std::vector<double>& W,
    const std::vector<double>& min_ratio,
    double lambda = 1e-6,
    double scaling = 100.0
);

SolutionResult_T1 Solver_CPLEX_FixedRoutes(
    int V,
    int M,
    int Q,
    double total_time_limit,
    std::vector<int> C,
    std::vector<int> Y_I,
    std::vector<int> Y_R,
    const std::vector<std::vector<double>>& dist,
    const std::vector<std::vector<int>>& Routes,
    const std::vector<double>& W,
    const std::vector<double>& min_ratio,
    double lambda = 1e-6,
    double scaling = 100.0
);

SolutionResult_T1 Solver_CPLEX_RefPenalty(
    int V,
    int M,
    int Q,
    double total_time_limit,
    std::vector<int> C,
    std::vector<int> Y_I,
    std::vector<int> Y_R,
    const std::vector<std::vector<double>>& dist,
    const std::vector<double>& W,
    double scaling = 1.0
);

SolutionResult_T2 LU_Model2_Solver_CPLEX(
    int num_station,
    int num_veh,
    const std::vector<int>& len_veh,
    const std::vector<std::vector<int>>& state_veh,
    int capacity_veh,
    const std::vector<int>& capacity_station,
    const std::vector<int>& initial_inventory_veh,
    const std::vector<int>& initial_inventory_station,
    const std::vector<int>& initial_r_demand,
    double l_const,
    double u_const
);
