#pragma once

#include <vector>
#include <string>

struct InstanceData {
    int V;
    int M;
    std::vector<int> Q;
    std::vector<int> s;
    std::vector<int> c;
    std::vector<int> Target;
    std::vector<double> weights;
    std::vector<double> min_ratio;
    int MAX_tour_Len;
    std::vector<double> pl;
    std::vector<double> pu;
    std::vector<std::vector<double>> dist;
    double total_time_limit;
    double load_time_unit = 60.0;
    double unload_time_unit = 60.0;
};

struct InstanceDataWR {
    int V;
    int M;
    int Q;
    double Time;
    std::vector<int> s;
    std::vector<int> c;
    std::vector<int> target;
    std::vector<double> weights;
    std::vector<double> min_ratio;
    std::vector<std::vector<double>> dist;
    std::vector<std::vector<int>> Routes;
};

InstanceData generate_multi_vehicle_instance(int V, int M, int Q0, double Time);

InstanceDataWR generate_wr_sample(int V, int M, int Q0, double Time);

std::vector<InstanceData> load_set_test_data(const int file_folder, const double timei);

InstanceData load_test_data(const int file_folder, const int file_number, const double timei);
InstanceData load_test_data_from_path(const std::string& filepath, const double timei);
bool generate_sample_file(int V, int M, int Q0, int coord_range, const std::string& filepath);
