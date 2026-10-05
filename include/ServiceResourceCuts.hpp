#pragma once
#include "FleetEventCuts.hpp"
#include <array>
#include <cstdint>
namespace ebrp {
using ServiceWeight = std::array<long long,3>; // p,d,z exact integer profits
struct ServiceSupport {
    bool valid=false;
    std::string reason;
    long long upper=0;
    int vehicle=0, resource_limit=0;
    std::vector<ServiceWeight> weights;
    std::vector<int> stations, pickup_caps;
    std::vector<long long> level_maxima;
};
struct ServiceContract {
    FleetContract resource;
    std::vector<std::vector<std::array<int,3>>> columns;
    bool valid=false;
    std::string reason,identity;
};
struct ServiceCut {
    std::vector<int> indices;
    std::vector<double> coefficients;
    std::vector<ServiceSupport> proofs;
    double rhs=0,activity_lower=0,violation_lower=0;
    std::string key;
};
struct ServiceStatistics {
    long long directions=0,dp_calls=0,cache_hits=0,reliable=0,unsupported=0;
    std::string contract;
    std::map<std::string,ServiceSupport> cache;
    std::deque<std::string> order;
};
ServiceContract prepareServiceContract(const Instance&,const NativeOtB1LinearModel&);
ServiceSupport proveServiceSupport(const FleetContract&,int,const std::vector<ServiceWeight>&);
std::vector<ServiceCut> separateServiceResources(const ServiceContract&,const std::vector<double>&,
    double,ServiceStatistics&);
std::string serviceSupportJson(const ServiceSupport&);
std::string serviceContractJson(const ServiceContract&);
} // namespace ebrp
