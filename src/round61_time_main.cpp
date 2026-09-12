#include "Round61TimeOracle.hpp"
#include "Parser.hpp"
#include <iostream>
#include <sstream>
#include <stdexcept>

int main(int argc,char** argv) {
    try {
        std::string input,inventory,mode="mip"; double T=3600,pick=60,drop=60,lambda=.15;
        ebrp::Round61TimeRequest r;
        for(int i=1;i<argc;++i) {
            std::string a=argv[i]; auto val=[&]() { if(++i>=argc) throw std::runtime_error("missing value"); return std::string(argv[i]); };
            if(a=="--input") input=val(); else if(a=="--inventory") inventory=val();
            else if(a=="--out") r.directory=val(); else if(a=="--mode") mode=val();
            else if(a=="--T") T=std::stod(val()); else if(a=="--pickup-time") pick=std::stod(val());
            else if(a=="--drop-time") drop=std::stod(val()); else if(a=="--lambda") lambda=std::stod(val());
            else if(a=="--cap") r.process_cap_seconds=std::stod(val()); else throw std::runtime_error("unknown argument "+a);
        }
        if(mode!="mip" && mode!="lp" && mode!="build") throw std::runtime_error("invalid oracle mode");
        auto in=ebrp::parseInstanceFile(input,T,pick,drop);
        std::istringstream s(inventory); std::string token;
        while(std::getline(s,token,',')) r.inventory.push_back(std::stoi(token));
        r.lp=mode=="lp";
        if(mode=="build") { ebrp::writeRound61TimeModel(in,r); return 0; }
        auto out=ebrp::solveRound61TimeOracle(in,lambda,r);
        std::cout<<out.classification<<" ["<<out.lower<<","<<out.upper<<"] seconds="<<out.seconds<<'\n';
        return 0;
    } catch(const std::exception& e) { std::cerr<<e.what()<<'\n'; return 1; }
}
