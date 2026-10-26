#include "ServiceResourceHull.hpp"
#include <cmath>
#include <iostream>
#include <stdexcept>
using namespace ebrp;
void require(bool a,const char* why){if(!a)throw std::runtime_error(why);}
ServiceContract fixture(){Instance in;in.V=1;in.M=1;in.Q={1};in.total_time_limit=0;in.pickup_time=in.drop_time=0;
    in.initial={0,1};in.capacity={0,1};in.dist.assign(2,std::vector<double>(2,0));
    ServiceContract c;c.valid=true;c.resource=physicalFleetContract(in);c.columns={{{-1,-1,-1},{0,1,2}}};return c;}
int main(){try{
    auto c=fixture();ServicePoint v(2,{0,0,0});v[1]={.5,0,.5};int calls=0;
    auto inside=classifyServiceHull(c,0,v,[&](const auto& library){HullMaster m;m.optimal=true;m.distance=1.;m.direction={{0,0,0},{0,0,1}};
        if(library.size()==1)m.lambda={1.};else m.lambda={.5,.5};++calls;return m;});
    require(inside.status=="INSIDE"&&calls==2&&inside.dp_calls==1,"restricted positive distance is not outside proof; combination closes");
    require(inside.distance_upper<1e-8&&inside.plans.size()==2,"explicit normalized combination");
    std::vector<ServicePlan> bank={{{0,0,0},{1,0,1}}};int seeded_calls=0;
    auto seeded=classifyServiceHull(c,0,v,[&](const auto& library){
        require(library.size()==2,"self-paid seed restored");HullMaster m;m.optimal=true;m.lambda={.5,.5};
        m.direction.resize(2,{0,0,0});++seeded_calls;return m;},{},1e-8,{},&bank);
    require(seeded.status=="INSIDE"&&seeded_calls==1&&seeded.dp_calls==0,"paid bank closes by verified combination");
    bool bad_seed=false;std::vector<ServicePlan> invalid_bank={{{0,0,0},{2,0,1}}};
    try{classifyServiceHull(c,0,v,[](const auto&){return HullMaster{};},{},1e-8,{},&invalid_bank);}catch(...){bad_seed=true;}
    require(bad_seed,"invalid paid seed rejected before master");
    v[1]={1,0,0};auto outside=classifyServiceHull(c,0,v,[](const auto&){HullMaster m;m.optimal=true;m.lambda={1.};m.direction={{0,0,0},{.5,0,-.5}};return m;});
    require(outside.status=="OUTSIDE"&&outside.cut.rhs==0&&outside.cut.violation_lower>.49,"signed full-domain support separation");
    require(outside.cut.proofs[0].valid,"attaining support certificate");
    v[1]={.5,0,.5};auto unknown=classifyServiceHull(c,0,v,[](const auto&){HullMaster m;m.optimal=true;m.lambda={1.};m.direction={{0,0,0},{0,0,0}};return m;});
    require(unknown.status=="UNKNOWN"&&unknown.reason=="duplicate_without_membership","duplicate pricing is unknown");
    v[1]={.5,.01,.5};auto fixed=classifyServiceHull(c,0,v,[](const auto&){throw std::runtime_error("must not run");return HullMaster{};});
    require(fixed.status=="UNKNOWN"&&fixed.reason=="zero_width_residual"&&!fixed.lp_calls,"zero width checked before LP");
    v[1]={0,0,0};auto zero=classifyServiceHull(c,0,v,[](const auto&){HullMaster m;m.optimal=true;m.lambda={1.};m.direction.resize(2,{0,0,0});return m;});
    require(zero.status=="INSIDE"&&!zero.dp_calls,"empty legitimate plan");
    v[1]={.5,0,.5};auto interrupted=classifyServiceHull(c,0,v,[](const auto&){return HullMaster{};});
    require(interrupted.status=="UNKNOWN"&&!std::isfinite(interrupted.distance_upper),"incomplete master cannot claim membership or zero distance");
    bool threw=false;c.resource.handling_lower=-1;
    try{classifyServiceHull(c,0,v,[](const auto&){HullMaster m;m.optimal=true;m.lambda={1.};m.direction={{0,0,0},{0,0,1}};return m;});}catch(const std::exception&){threw=true;}
    require(threw,"invalid physical contract is a failure");
    std::cout << "9 hull certification/UNKNOWN/fault/paid-bank fixtures passed; injected master, Optimize=0\n";return 0;
}catch(const std::exception& e){std::cerr << e.what() << '\n';return 1;}}
