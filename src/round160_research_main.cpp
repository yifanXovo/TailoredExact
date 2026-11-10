#include "Round160PhysicalNeighborhood.hpp"
#include "Parser.hpp"
#include <chrono>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

int main(int argc,char** argv) {
    try {
        if(argc<9)throw std::runtime_error("Round160Research input T pickup drop lambda parent.txt out seconds [nodes] [passes] [qualify|owner-fixed|uncompressed] [block stations...]");
        auto began=std::chrono::steady_clock::now();
        auto data=ebrp::parseInstanceFile(argv[1],std::stod(argv[2]),std::stod(argv[3]),std::stod(argv[4]));
        std::ifstream in(argv[6]);if(!in)throw std::runtime_error("cannot read parent");
        int count;in>>count;std::vector<ebrp::RoutePlan> routes;
        for(int k=0;k<count;++k){ebrp::RoutePlan r;int n;in>>r.vehicle>>n;r.nodes.resize(n);for(auto& i:r.nodes)in>>i;
            for(int p=1;p+1<n;++p){int delta;in>>delta;r.operations.push_back({r.nodes[p],std::max(0,delta),std::max(0,-delta)});}routes.push_back(r);}
        if(!in)throw std::runtime_error("truncated parent");
        ebrp::round160::Config cfg;
        if(argc>9)cfg.nodes=std::stoi(argv[9]);
        if(argc>10)cfg.passes=std::stoi(argv[10]);
        if(argc>11){std::string mode=argv[11];cfg.qualify_only=mode=="qualify";cfg.fixed_old_owner=mode=="owner-fixed";cfg.uncompressed=mode=="uncompressed";}
        for(int j=12;j<argc;++j)cfg.block.push_back(std::stoi(argv[j]));
        double cap=std::stod(argv[8]);auto remaining=[&](){return cap-std::chrono::duration<double>(std::chrono::steady_clock::now()-began).count();};
        auto result=ebrp::round160::optimize(data,std::stod(argv[5]),routes,argv[7],cfg,remaining);
        std::cout<<"Round160 returned "<<result.calls<<" calls, "<<result.improvements<<" improvements\n";
        return 0;
    } catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
