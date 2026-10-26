#include "ServiceResourceCuts.hpp"
#include "Parser.hpp"
#include <fstream>
#include <iomanip>
#include <iostream>
#include <chrono>
// Persistent stdin oracle. One audited actual-matrix contract, then arbitrary
// signed integer weight requests. Each response contains a full-domain upper
// and a verified attaining plan. No Optimize and no physical-route UB.
int main(int argc,char**argv){try{
    if(argc!=6)throw std::runtime_error("input T pickup drop typed_matrix");
    auto in=ebrp::parseInstanceFile(argv[1],std::stod(argv[2]),std::stod(argv[3]),std::stod(argv[4]));
    std::ifstream f(argv[5]);int n=0,R=0;ebrp::NativeOtB1LinearModel m;
    if(!(f>>n>>R)||n<1||R<1)throw std::runtime_error("matrix header");
    for(int j=0;j<n;++j){std::string name;char t;double l,u;if(!(f>>name>>t>>l>>u))throw std::runtime_error("matrix column");m.names.push_back(name);m.types.push_back(t);m.lower_bounds.push_back(l);m.upper_bounds.push_back(u);}
    m.row_starts.push_back(0);for(int r=0;r<R;++r){char sense;double rhs;int count;if(!(f>>sense>>rhs>>count)||count<0)throw std::runtime_error("matrix row");m.senses.push_back(sense);m.rhs.push_back(rhs);
        for(int t=0;t<count;++t){int j;double a;if(!(f>>j>>a)||j<0||j>=n)throw std::runtime_error("matrix term");m.column_indices.push_back(j);m.coefficients.push_back(a);}m.row_starts.push_back(static_cast<int>(m.coefficients.size()));}
    if(!f)throw std::runtime_error("matrix parse");
    auto c=ebrp::prepareServiceContract(in,m);if(!c.valid)throw std::runtime_error(c.reason);
    std::cout<<std::setprecision(17)<<ebrp::serviceContractJson(c)<<std::endl;
    std::string command;while(std::cin>>command){std::vector<int> anchors;int k=0;
        if(command=="A"){int count=0;if(!(std::cin>>k>>count)||count<0||count>3)throw std::runtime_error("anchor request");anchors.resize(count);for(auto&i:anchors)std::cin>>i;}
        else k=std::stoi(command);
        if(k<0)break;std::vector<ebrp::ServiceWeight>w(in.V+1,{0,0,0});
        for(int i=1;i<=in.V;++i)for(int t=0;t<3;++t)std::cin>>w[i][t];if(!std::cin)throw std::runtime_error("weight parse");
        const auto tick=std::chrono::steady_clock::now();auto r=ebrp::proveServiceSupport(c.resource,k,w,true,anchors);
        if(!r.valid)throw std::runtime_error(r.reason);
        std::cout<<"{\"seconds\":"<<std::chrono::duration<double>(std::chrono::steady_clock::now()-tick).count()<<",\"proof\":"<<ebrp::serviceSupportJson(r)<<"}"<<std::endl;}
    return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
