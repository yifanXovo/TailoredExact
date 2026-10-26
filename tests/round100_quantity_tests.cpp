#include "CanonicalCompactModel.hpp"
#include "CplexBaseline.hpp"
#include "PaperK1AmSf.hpp"
#include "Round98StateService.hpp"
#include <iostream>
#include <limits>
#include <stdexcept>
#include <unordered_map>
void require(bool x,const char* why){if(!x)throw std::runtime_error(why);}
int main(int argc,char** argv){try{
    require(argc==2,"exclusive destination required");const std::filesystem::path dir(argv[1]);
    require(std::filesystem::create_directories(dir),"destination already exists");
    ebrp::Instance in;in.V=3;in.M=2;in.Q={2,3};in.initial={0,0,3,4};in.capacity={0,0,5,4};
    in.target={0,1,2,3};in.weights={0,1,1,1};in.min_ratio={0,0,0,0};
    in.dist.assign(4,std::vector<double>(4,1));for(int i=0;i<=3;++i)in.dist[i][i]=0;
    in.total_time_limit=100;in.pickup_time=0;in.drop_time=0;
    ebrp::SolveOptions o;require(!o.round100_continuous_quantities,"default changed");
    ebrp::configurePaperK1AmSfOverrides(o);o.method="gcap-frontier";o.algorithm_preset="research-round83-vds-equal-net-exchange";
    o.external_gini_interval_mip_policy="round55-vd-p";o.round100_continuous_quantities=true;
    require(ebrp::round98IsIsolatedENS(o),"ENS-Q admission");
    auto bad=o;bad.round98_state_service="m-binary";require(!ebrp::round98IsIsolatedENS(bad),"AB mixing admitted");
    bad=o;bad.plain_baseline=true;require(!ebrp::round98IsIsolatedENS(bad),"P mixing admitted");
    bad=o;bad.round97_native_closure="feedback";require(!ebrp::round98IsIsolatedENS(bad),"feedback admitted");
    ebrp::CanonicalCompactModelSpec s;s.strengthened=true;s.interval_restricted=true;s.gamma_U=2.0/3;
    s.station_state_formulation="vd-p";s.round51_subset_duration_big_m="off";
    require(ebrp::writeCanonicalCompactModel(in,o,dir/"ENS-Q.lp",s).written,"base writer");
    o.round100_continuous_quantities=false;
    require(ebrp::writeCanonicalCompactModel(in,o,dir/"ENS-C.lp",s).written,"base ENS writer");
    auto forced=in;forced.V=2;forced.M=1;forced.Q={3};forced.initial={0,0,3};forced.capacity={0,3,3};
    forced.target={0,1,1};forced.weights={0,1,1};forced.min_ratio={0,0,0};
    forced.dist.assign(3,std::vector<double>(3,1));for(int i=0;i<3;++i)forced.dist[i][i]=0;
    s.gamma_U=0;s.add_verified_incumbent_row=true;s.verified_incumbent=.01;
    o.round100_continuous_quantities=true;
    require(ebrp::writeCanonicalCompactModel(forced,o,dir/"ENS-Q_forced.lp",s).written,"singleton/absent initial");
    forced.total_time_limit=0;
    require(ebrp::writeCanonicalCompactModel(forced,o,dir/"ENS-Q_empty.lp",s).written,"empty domain");
    std::unordered_map<std::string,double> values;
    for(int k=0;k<in.M;++k)for(int i=1;i<=in.V;++i)for(const auto& prefix:{"p_","d_"})
        values[std::string(prefix)+std::to_string(k)+"_"+std::to_string(i)]=0;
    require(ebrp::reconstructCanonicalCompactRoutes(in,values,true).size()==2,"unvisited zero vector");
    auto rejects=[&](const std::unordered_map<std::string,double>& v){try{ebrp::reconstructCanonicalCompactRoutes(in,v,true);return false;}catch(const std::exception&){return true;}};
    for(double x:{.25,-.25,3.,std::numeric_limits<double>::infinity(),std::numeric_limits<double>::quiet_NaN()}){
        auto v=values;v["p_0_2"]=x;require(rejects(v),"invalid unvisited pickup accepted");
    }
    auto missing=values;missing.erase("d_1_3");require(rejects(missing),"missing column accepted");
    auto zeroCap=values;zeroCap["d_1_3"]=1;require(rejects(zeroCap),"zero cap accepted");
    std::cout<<"ENS-Q fixtures=4 all-column guards passed Optimize=0\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
