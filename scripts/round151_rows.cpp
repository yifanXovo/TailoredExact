#include "Round151Research.hpp"
#include <iostream>
using namespace ebrp;
int main(int argc,char** argv){try{
    if(argc!=2)throw std::runtime_error("scope file required");
    std::ifstream f(argv[1]);int n;long long bm,b;double cutoff,upper;std::string mode;
    f>>n>>bm>>b>>cutoff>>upper>>mode;
    std::vector<std::vector<int>> s(n+1);std::vector<double> c(n+1),w(n+1);
    for(int i=1;i<=n;++i){int m;f>>c[i]>>w[i]>>m;s[i].resize(m);for(int& y:s[i])f>>y;}
    if(!f)throw std::runtime_error("scope parse");
    const auto caps=round151_detail::caps(s,c,w,bm,b,cutoff,upper);
    const auto rows=round151_detail::rows(caps,s,upper,mode);
    std::cout<<'{';round151_detail::dump(std::cout,caps);std::cout<<",\"rows\":[";
    bool first=true;for(const auto& r:rows){if(!first)std::cout<<',';first=false;
        std::cout<<"{\"name\":"<<std::quoted(r.name)<<",\"sense\":\"<\",\"rhs\":0,\"terms\":{";
        bool term=true;for(const auto& t:r.coefficients){if(!term)std::cout<<',';term=false;std::cout<<std::quoted(t.first)<<':'<<t.second;}
        std::cout<<"}}";}
    std::cout<<"]}\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
