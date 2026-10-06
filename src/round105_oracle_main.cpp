#include "Round105Decomposition.hpp"
#include "Parser.hpp"
#include <chrono>
#include <fstream>
#include <iostream>
#include <stdexcept>
int main(int argc,char** argv) {
    try {
        if(argc!=11)throw std::runtime_error("usage: Round105Oracle input T cp cd lambda vehicle pattern.txt output cap core(0/1)");
        auto in=ebrp::parseInstanceFile(argv[1],std::stod(argv[2]),std::stod(argv[3]),std::stod(argv[4]));
        ebrp::Round105Pattern p;p.vehicle=std::stoi(argv[6]);p.operation.assign(in.V+1,0);
        std::ifstream f(argv[7]);for(int i=1;i<=in.V;++i)if(!(f>>p.operation[i]))throw std::runtime_error("missing complete operation");
        int extra=0;if(f>>extra)throw std::runtime_error("extra operation");
        ebrp::SolveOptions opt;opt.lambda=std::stod(argv[5]);opt.gurobi_home="D:/gurobi1302/win64";
        opt.process_start_time=std::chrono::steady_clock::now();opt.process_start_time_valid=true;
        opt.process_wall_time_limit=std::stod(argv[9]);opt.process_shutdown_margin_seconds=0;
        auto r=ebrp::solveRound105OracleDiagnostic(in,opt,p,argv[8],std::stoi(argv[10])!=0);
        std::ofstream out(std::filesystem::path(argv[8])/"result.json");
        out<<"{\"status\":"<<static_cast<int>(r.status)<<",\"core_confirmed\":"<<(r.core_confirmed ? "true" : "false")<<",\"core\":[";
        for(std::size_t i=0;i<r.core.size();++i){if(i)out<<',';out<<r.core[i];}out<<"],\"reason\":\""<<r.reason<<"\"}\n";
        std::cout<<"oracle_status="<<static_cast<int>(r.status)<<'\n';
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}return 0;
}
