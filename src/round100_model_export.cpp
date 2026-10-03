// Zero Optimize, exactly the three quantity/AB study identities.
#include "CanonicalCompactModel.hpp"
#include "PaperK1AmSf.hpp"
#include "Parser.hpp"
#include <fstream>
#include <iostream>
int main(int argc,char** argv){try{
    if(argc!=10)throw std::runtime_error("input T pickup drop lambda gL gU cutoff directory");
    auto in=ebrp::parseInstanceFile(argv[1],std::stod(argv[2]),std::stod(argv[3]),std::stod(argv[4]));
    ebrp::SolveOptions opt;ebrp::configurePaperK1AmSfOverrides(opt);opt.lambda=std::stod(argv[5]);
    ebrp::CanonicalCompactModelSpec s;s.strengthened=true;s.interval_restricted=true;
    s.gamma_L=std::stod(argv[6]);s.gamma_U=std::stod(argv[7]);s.add_verified_incumbent_row=true;
    s.verified_incumbent=std::stod(argv[8]);s.station_state_formulation="vd-p";s.round51_subset_duration_big_m="off";
    const std::filesystem::path dir(argv[9]);
    if(!std::filesystem::create_directories(dir))throw std::runtime_error("exclusive destination required");
    for(const auto& arm:{"ENS-C","ENS-Q","M-B"}){
        opt.round100_continuous_quantities=std::string(arm)=="ENS-Q";
        opt.round98_state_service=std::string(arm)=="M-B"?"m-binary":"off";
        auto a=ebrp::writeCanonicalCompactModel(in,opt,dir/(std::string(arm)+".lp"),s);
        if(!a.written)throw std::runtime_error(a.failure_reason);
        std::ofstream f(dir/(std::string(arm)+".json"));
        f<<"{\"optimizer_calls\":0,\"arm\":\""<<arm<<"\",\"sha256\":\""<<a.sha256
         <<"\",\"rows\":"<<a.rows<<",\"columns\":"<<a.columns<<",\"nonzeros\":"<<a.nonzeros<<"}\n";
        if(!f)throw std::runtime_error("receipt write failed");
    }return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
