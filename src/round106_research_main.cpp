#include "Round106Research.hpp"
#include "Parser.hpp"
#include "PaperK1AmSf.hpp"
#include <fstream>
#include <iostream>
#include <stdexcept>
using namespace ebrp;
int main(int argc,char** argv) {
    try {
        if(argc<9)throw std::runtime_error("replay|fleet input T pick drop lambda out cap [strategy master candidate legalStart | inventory]");
        const auto in=parseInstanceFile(argv[2],std::stod(argv[3]),std::stod(argv[4]),std::stod(argv[5]));
        SolveOptions o;configurePaperK1AmSfOverrides(o);o.lambda=std::stod(argv[6]);
        o.gurobi_home="D:/gurobi1302/win64";o.external_gini_artifact_dir=argv[7];
        o.process_wall_time_limit=std::stod(argv[8]);o.process_shutdown_margin_seconds=0;
        o.process_start_time=std::chrono::steady_clock::now();o.process_start_time_valid=true;
        if(std::string(argv[1])=="replay"&&argc==13) {
            o.round106_events=argv[9];const auto r=round106Replay(in,o,argv[10],argv[11],argv[12]);
            if(r.status=="error")throw std::runtime_error(r.strict_certificate_rejection_reason);
            std::cout<<r.status<<" UB="<<r.upper_bound<<" LB="<<r.lower_bound<<'\n';
        }else if(std::string(argv[1])=="contracts"&&argc==13) {
            round106AdapterContracts(in,o,argv[9],argv[10],argv[11],argv[12]);
            std::cout<<"scripted audited-vector contracts PASS\n";
        }else if(std::string(argv[1])=="fleet"&&argc==10) {
            o.process_shutdown_margin_seconds=30;
            auto Y=in.initial;std::ifstream f(argv[9]);
            for(int i=1;i<=in.V;++i)if(!(f>>Y[i]))throw std::runtime_error("inventory dimensions");
            std::string extra;if(f>>extra)throw std::runtime_error("inventory extra value");
            std::cout<<round106FixedFleet(in,o,Y)<<'\n';
        }else throw std::runtime_error("argument count/mode");
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}return 0;
}
