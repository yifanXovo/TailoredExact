#include "ObjectiveResourceCompression.hpp"
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
int main(int argc,char**argv){try{
    if(argc!=3)throw std::runtime_error("usage: Round104Compression pool.txt grouped|fleet");
    std::ifstream f(argv[1]);std::string scope;int n=0,m=0;f>>scope>>n>>m;
    if(!f||n<=0||n>1000000||m<0||m>1000000)throw std::runtime_error("input dimensions");
    std::vector<double> lower(n),upper(n);for(int i=0;i<n;++i)f>>lower[i]>>upper[i];
    std::vector<ebrp::ObjectiveResourceRow> rows(m);
    for(auto&r:rows){int nz=0;r.scope=scope;f>>r.vehicle>>r.multiplier>>r.rhs>>nz;
        if(nz<0||nz>n)throw std::runtime_error("input nonzeros");
        r.indices.resize(nz);r.coefficients.resize(nz);
        for(int j=0;j<nz;++j)f>>r.indices[j]>>r.coefficients[j];}
    if(!f)throw std::runtime_error("input read failed");
    const std::string mode=argv[2];if(mode!="grouped"&&mode!="fleet")throw std::runtime_error("mode");
    const auto out=ebrp::compressObjectiveResources(rows,lower,upper,mode=="fleet");
    std::cout<<std::setprecision(17)<<"{\"rows\":[";
    for(std::size_t j=0;j<out.size();++j){if(j)std::cout<<',';const auto&r=out[j];
        std::cout<<"{\"vehicle\":"<<r.vehicle<<",\"rhs\":"<<r.rhs<<",\"compensation_upper\":"<<r.compensation_upper<<",\"coefficients\":[";
        for(std::size_t t=0;t<r.indices.size();++t){if(t)std::cout<<',';std::cout<<'['<<r.indices[t]<<','<<r.coefficients[t]<<']';}
        std::cout<<"],\"source_rows\":[";
        for(std::size_t t=0;t<r.source_rows.size();++t){if(t)std::cout<<',';std::cout<<r.source_rows[t];}std::cout<<"]}";}
    std::cout<<"]}\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
