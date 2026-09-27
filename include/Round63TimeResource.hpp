#pragma once
#include "Instance.hpp"
#include <filesystem>
#include <map>
#include <ostream>
#include <set>

namespace ebrp {
// Coefficients are in max(1,T) time units. Supplies round down, capacities up.
// The identity includes every physical coefficient, Q and service domain.
struct Round63TimeData {
    int V=0,M=0;
    double scale=1,handling=0;
    std::vector<std::vector<double>> travel,upper,shortest;
    std::string identity;
};
struct Round63TimePoint {
    std::vector<std::vector<std::vector<double>>> x;
    std::vector<std::vector<double>> pickup;
};
struct Round63TimeCut {
    int vehicle=0;
    std::vector<int> support;
    std::map<std::string,double> coefficients;
    double violation=0,source_capacity=0,mincut=0;
    bool violated=false;
    std::string signature,identity,scope="original_physical_global";
};
Round63TimeData prepareRound63Time(const Instance&);
Round63TimePoint emptyRound63TimePoint(const Round63TimeData&);
Round63TimeCut round63TimeRow(const Round63TimeData&,int,const std::vector<int>&);
double evaluateRound63TimeRow(const Round63TimeData&,const Round63TimePoint&,const Round63TimeCut&);
Round63TimeCut separateRound63Time(const Round63TimeData&,const Round63TimePoint&,int,double tolerance=1e-7);
bool acceptRound63TimeCut(const Round63TimeData&,const Round63TimeCut&,std::set<std::string>&);
bool validRound63TimeMode(const std::string&);
void appendRound63TimeModel(const Instance&,const std::filesystem::path&,const std::string&);
void writeRound63TimeData(const Round63TimeData&,const std::filesystem::path&);
void writeRound63TimeCut(const Round63TimeCut&,std::ostream&,long long query,double node,int api_return);
} // namespace ebrp
