#include "CanonicalCompactModel.hpp"
#include "PaperK1AmSf.hpp"
#include "Round98StateService.hpp"
#include <iostream>
#include <stdexcept>
void require(bool x,const char* why){if(!x)throw std::runtime_error(why);}
int main(int argc,char** argv){try{
    require(argc==2,"exclusive destination required");const std::filesystem::path dir(argv[1]);
    require(std::filesystem::create_directories(dir),"destination already exists");
    ebrp::Instance in;in.V=3;in.M=2;in.Q={2,3};in.initial={0,0,3,4};
    in.capacity={0,0,5,4};in.target={0,1,2,3};in.weights={0,1,1,1};in.min_ratio={0,0,0,0};
    in.dist.assign(4,std::vector<double>(4,1));for(int i=0;i<=3;++i)in.dist[i][i]=0;
    in.total_time_limit=100;in.pickup_time=0;in.drop_time=0;
    ebrp::SolveOptions o;ebrp::configurePaperK1AmSfOverrides(o);
    auto admission=o;admission.method="gcap-frontier";admission.algorithm_preset="research-round83-vds-equal-net-exchange";
    admission.external_gini_interval_mip_policy="round55-vd-p";
    ebrp::CanonicalCompactModelSpec s;s.strengthened=true;s.interval_restricted=true;
    s.gamma_U=2.0/3;s.station_state_formulation="vd-p";s.round51_subset_duration_big_m="off";
    for(const auto& mode:{"aggregate","q-integer","m-binary","projected","m-binary-linked"}){
        admission.round98_state_service=mode;require(ebrp::round98IsIsolatedENS(admission),"mode not admitted");
        auto bad=admission;bad.round97_native_closure="feedback";require(!ebrp::round98IsIsolatedENS(bad),"feedback admitted");
        o.round98_state_service=mode;
        auto a=ebrp::writeCanonicalCompactModel(in,o,dir/(std::string(mode)+".lp"),s);require(a.written,"base export failed");
    }
    auto forced=in;forced.V=2;forced.M=1;forced.Q={3};forced.initial={0,0,3};forced.capacity={0,3,3};
    forced.target={0,1,1};forced.weights={0,1,1};forced.min_ratio={0,0,0};
    forced.dist.assign(3,std::vector<double>(3,1));for(int i=0;i<3;++i)forced.dist[i][i]=0;
    s.gamma_U=0;s.add_verified_incumbent_row=true;s.verified_incumbent=.01;
    for(const auto& mode:{"q-integer","m-binary","m-binary-linked"}){
        o.round98_state_service=mode;
        require(ebrp::writeCanonicalCompactModel(forced,o,dir/(std::string(mode)+"_forced.lp"),s).written,"forced export failed");
        auto empty=forced;empty.total_time_limit=0;
        require(ebrp::writeCanonicalCompactModel(empty,o,dir/(std::string(mode)+"_empty.lp"),s).written,"empty export failed");
    }
    require(ebrp::round98ProjectsDirection("q-integer")&&!ebrp::round98ContinuousQuantities("q-integer"),"Q-I coupling");
    require(!ebrp::round98ProjectsDirection("m-binary")&&ebrp::round98ContinuousQuantities("m-binary"),"M-B coupling");
    require(!ebrp::round98KnownStateService("unknown"),"unknown mode accepted");
    require(ebrp::round99LinksDirection("m-binary-linked")&&!ebrp::round98ProjectsDirection("m-binary-linked")&&ebrp::round98ContinuousQuantities("m-binary-linked"),"linked direction traits");
    std::cout<<"new_modes=3 fixtures=11 optimizer_calls=0\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
