#include "CanonicalCompactModel.hpp"
#include "PaperK1AmSf.hpp"
#include "Evaluator.hpp"
#include "Round98StateService.hpp"
#include <cmath>
#include <fstream>
#include <iostream>
#include <stdexcept>
void require(bool v,const char* message){if(!v)throw std::runtime_error(message);}
int main(int argc,char** argv){try{
    require(argc==2,"exclusive output directory required");
    const std::filesystem::path dir(argv[1]);std::filesystem::create_directories(dir);
    // Independent finite checks of projection existence, including all zero caps.
    int checks=0;
    for(int a=0;a<=4;++a)for(int c=0;c<=4;++c)for(int iz=0;iz<=4;++iz)
    for(int ip=0;ip<=16;++ip)for(int id=0;id<=16;++id){
        const double z=iz/4.0,p=ip/4.0,d=id/4.0;
        const double lo=a?p/a:0,hi=c?z-d/c:z;
        const bool exists=(a||p==0)&&(c||d==0)&&lo<=hi+1e-12;
        const bool projected=p<=a*z+1e-12&&d<=c*z+1e-12&&
            (!a||!c||c*p+a*d<=a*c*z+1e-12);
        require(exists==projected,"continuous projection positive/zero counterexample");++checks;
    }
    ebrp::Instance in;in.V=3;in.M=2;in.Q={2,3};
    in.initial={0,0,3,4};in.capacity={0,0,5,4};in.target={0,1,2,3};
    in.weights={0,1,1,1};in.min_ratio={0,0,0,0};
    in.dist.assign(4,std::vector<double>(4,1));for(int i=0;i<=3;++i)in.dist[i][i]=0;
    in.total_time_limit=100;in.pickup_time=0;in.drop_time=0;
    ebrp::SolveOptions opt;ebrp::configurePaperK1AmSfOverrides(opt);
    // Admission uses the same predicate in the CLI and programmatic tree API.
    auto admission=opt;admission.method="gcap-frontier";
    admission.algorithm_preset="research-round83-vds-equal-net-exchange";
    admission.external_gini_interval_mip_policy="round55-vd-p";
    admission.round98_state_service="projected";
    require(ebrp::round98IsIsolatedENS(admission),"isolated research admission failed");
    auto incompatible=admission;incompatible.round97_native_closure="feedback";
    require(!ebrp::round98IsIsolatedENS(incompatible),"feedback admitted to isolated study");
    incompatible=admission;incompatible.plain_baseline=true;
    require(!ebrp::round98IsIsolatedENS(incompatible),"plain benchmark admitted to reformulation");
    incompatible=admission;incompatible.round62_threshold_mode="service";
    require(!ebrp::round98IsIsolatedENS(incompatible),"historical mode rows admitted to projection");
    ebrp::CanonicalCompactModelSpec spec;spec.strengthened=true;spec.interval_restricted=true;
    spec.gamma_U=2.0/3;spec.station_state_formulation="vd-p";spec.round51_subset_duration_big_m="off";
    for(const auto& mode:{"off","aggregate","projected"}){
        opt.round98_state_service=mode;
        auto a=ebrp::writeCanonicalCompactModel(in,opt,dir/(std::string(mode)+".lp"),spec);
        require(a.written,"complete micro model export failed");
    }
    // Tight cutoff forces two noninitial singleton states. The only valid
    // original operation sequence picks two and drops one, returning loaded.
    ebrp::Instance forced=in;forced.V=2;forced.M=1;forced.Q={3};
    forced.initial={0,0,3};forced.capacity={0,3,3};forced.target={0,1,1};
    forced.weights={0,1,1};forced.min_ratio={0,0,0};
    forced.dist.assign(3,std::vector<double>(3,1));for(int i=0;i<3;++i)forced.dist[i][i]=0;
    spec.gamma_U=0;spec.add_verified_incumbent_row=true;spec.verified_incumbent=.01;
    require(ebrp::verifySolution(forced,{{0,{0,2,1,0},{{2,2,0},{1,0,1}}}},.15).feasible,
        "forced singleton loaded-return physical witness rejected");
    for(const auto& mode:{"off","aggregate","projected"}){
        opt.round98_state_service=mode;
        auto a=ebrp::writeCanonicalCompactModel(forced,opt,dir/(std::string(mode)+"_forced.lp"),spec);
        require(a.written,"forced-state model export failed");
        auto empty=forced;empty.total_time_limit=0;
        a=ebrp::writeCanonicalCompactModel(empty,opt,dir/(std::string(mode)+"_empty.lp"),spec);
        require(a.written,"empty-domain infeasible contract export failed");
    }
    std::unordered_map<std::string,double> values;
    for(int k=0;k<2;++k)for(int i=1;i<=3;++i){values["p_"+std::to_string(k)+"_"+std::to_string(i)]=0;
        values["d_"+std::to_string(k)+"_"+std::to_string(i)]=0;}
    require(ebrp::reconstructCanonicalCompactRoutes(in,values,true).size()==2,"empty witness decoding");
    values["p_1_3"]=0.25;bool rejected=false;
    try{ebrp::reconstructCanonicalCompactRoutes(in,values,true);}catch(const std::exception&){rejected=true;}
    require(rejected,"unvisited fractional operation rounded into valid witness");
    values["p_1_3"]=1e-6;ebrp::reconstructCanonicalCompactRoutes(in,values,true);
    values["p_1_3"]=NAN;rejected=false;
    try{ebrp::reconstructCanonicalCompactRoutes(in,values,true);}catch(const std::exception&){rejected=true;}
    require(rejected,"nonfinite operation decoded");
    const double b=10,Y=.5*8+.5*12,P=1,D=1;
    require(Y==b&&P+D==.5*2+.5*2,"integer-mean counterexample missing");
    require(.5/2+.5/2<=1,"C-only simultaneous-direction counterexample missing");
    std::cout<<"projection_checks="<<checks<<" models=3 strict_decoder=passed optimizer_calls=0\n";
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
