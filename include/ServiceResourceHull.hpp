#pragma once
#include "ServiceResourceCuts.hpp"
#include <functional>
#include <limits>
namespace ebrp {
using ServicePlan=std::vector<std::array<int,3>>;
using ServicePoint=std::vector<std::array<double,3>>;
struct HullMaster {
    bool optimal=false;
    double distance=0;
    std::vector<double> lambda;
    ServicePoint direction;
};
using HullLpSolver=std::function<HullMaster(const std::vector<ServicePlan>&)>;
using HullTrace=std::function<void(const std::string&)>;
struct HullMembership {
    std::string status="UNKNOWN",reason;
    int lp_calls=0,dp_calls=0,duplicates=0;
    double distance_upper=std::numeric_limits<double>::infinity();
    std::vector<ServicePlan> plans;
    std::vector<double> lambda_raw; // mathematical weights: exact(raw)/sum exact(raw)
    ServiceCut cut;
};
// Full-domain certification, never based on a positive restricted LP distance.
HullMembership classifyServiceHull(const ServiceContract&,int,const ServicePoint&,
    const HullLpSolver&,const std::vector<int>& anchors={},double tolerance=1e-8,const HullTrace& trace={});
std::vector<int> chooseServiceAnchors(const FleetContract&,int,const HullMembership&);
std::string hullMembershipJson(const HullMembership&);
} // namespace ebrp
