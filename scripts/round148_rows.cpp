#include "Round148Research.hpp"
#include <iostream>
using namespace ebrp;
int main(int argc,char** argv){try{
    if(argc!=2)throw std::runtime_error("scope/primal file required");std::ifstream f(argv[1]);int n;long long bm,b;
    f>>n>>bm>>b;std::vector<std::vector<int>> support(n+1);std::vector<double> c(n+1);
    for(int i=1;i<=n;++i){int m;f>>c[i]>>m;support[i].resize(m);for(int& y:support[i])f>>y;}
    int size;f>>size;std::map<std::string,double> point;
    for(int k=0;k<size;++k){std::string name;double v;f>>name>>v;point[name]=v;}if(!f)throw std::runtime_error("scope parse");
    const auto gd=round146_detail::block(support,c,bm,b);
    std::cout<<std::setprecision(17)<<"{\"applicable\":"<<(gd.applicable?"true":"false")<<",\"old_GD_rows\":"<<gd.rows.size();
    if(gd.applicable){const auto s=round148_detail::select(gd,c,point);
        std::cout<<",\"row\":";round148_detail::emitRow(std::cout,s.row);
        std::cout<<",\"kind\":"<<std::quoted(s.kind)<<",\"S\":"<<s.S<<",\"violation\":"<<s.violation<<",\"seconds\":"<<s.seconds<<",\"slopes\":[";
        for(int i=1;i<=n;++i){if(i>1)std::cout<<',';std::cout<<s.slopes[i];}std::cout<<']';}
    std::cout<<"}\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
