#include "Round149Research.hpp"
#include <iostream>
using namespace ebrp;
int main(int argc,char** argv){try{
    if(argc!=2)throw std::runtime_error("scope file required");
    std::ifstream f(argv[1]);int n;long long bm,b;double cutoff,upper;
    f>>n>>bm>>b>>cutoff>>upper;std::vector<std::vector<int>> s(n+1);
    std::vector<double> c(n+1),w(n+1);
    for(int i=1;i<=n;++i){int m;f>>c[i]>>w[i]>>m;s[i].resize(m);for(int& y:s[i])f>>y;}
    if(!f)throw std::runtime_error("scope parse");
    const auto p=round149_detail::floor(s,c,w,bm,b);
    const double beta=std::min(upper,round149_detail::sub(round149_detail::val(cutoff),round149_detail::val(p.lower)).hi);
    round149_detail::require(beta>=0,"negative_beta");
    const auto rows=p.feasible&&p.lower>0?round149_detail::rows(s,beta,upper):std::vector<round143_detail::Row>{};
    std::cout<<std::setprecision(17)<<"{\"feasible\":"<<(p.feasible?"true":"false")
        <<",\"penalty_lower\":"<<p.lower<<",\"dual_lower\":"<<p.dual_lower
        <<",\"mu\":"<<p.mu<<",\"nu\":"<<p.nu<<",\"primal\":"<<p.primal
        <<",\"seconds\":"<<p.seconds<<",\"beta\":"<<beta<<",\"rows\":[";
    bool first=true;for(const auto& r:rows){if(!first)std::cout<<',';first=false;
        std::cout<<"{\"name\":"<<std::quoted(r.name)<<",\"sense\":\"<\",\"rhs\":0,\"terms\":{";
        bool term=true;for(const auto& t:r.coefficients){if(!term)std::cout<<',';term=false;std::cout<<std::quoted(t.first)<<':'<<t.second;}
        std::cout<<"}}";
    }
    std::cout<<"]}\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
