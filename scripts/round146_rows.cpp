#include "Round146Research.hpp"
#include <iostream>
using namespace ebrp;
int main(int argc,char** argv){try{
    if(argc!=2)throw std::runtime_error("scope file required");std::ifstream f(argv[1]);int n,conditional;long long bm,b;
    f>>n>>bm>>b>>conditional;std::vector<std::vector<int>> support(n+1);std::vector<double> c(n+1);
    for(int i=1;i<=n;++i){int m;f>>c[i]>>m;support[i].resize(m);for(int& y:support[i])f>>y;}
    if(!f)throw std::runtime_error("scope parse");const auto r=round146_detail::block(support,c,bm,b,conditional!=0);
    std::cout<<std::setprecision(17)<<"{\"applicable\":"<<(r.applicable?"true":"false")<<",\"infeasible\":"<<(r.infeasible?"true":"false")
        <<",\"lower\":"<<r.lower<<",\"upper\":"<<r.upper<<",\"seconds\":"<<r.seconds<<",\"states\":[";bool first=true;
    for(const auto& s:r.states){if(!first)std::cout<<',';first=false;std::cout<<"{\"i\":"<<s.i<<",\"y\":"<<s.y<<",\"feasible\":"<<(s.feasible?"true":"false")
        <<",\"lower\":"<<s.lower<<",\"upper\":"<<s.upper<<",\"low\":"<<s.low<<",\"high\":"<<s.high<<'}';}
    std::cout<<"],\"rows\":[";first=true;
    for(const auto& row:r.rows){if(!first)std::cout<<',';first=false;std::cout<<"{\"name\":"<<std::quoted(row.name)<<",\"sense\":\">\",\"rhs\":0,\"terms\":{";bool term_first=true;
        for(const auto& term:row.coefficients){if(!term_first)std::cout<<',';term_first=false;std::cout<<std::quoted(term.first)<<':'<<term.second;}std::cout<<"}}";}
    std::cout<<"]}\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
