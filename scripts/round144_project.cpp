// Small independent-input driver for exact Fraction vs production intervals.
#include "ObjectiveResourceCompression.hpp"
#include <fstream>
#include <iostream>
#include <iomanip>
int main(int argc,char** argv){try{
    if(argc!=2)throw std::runtime_error("input required");std::ifstream f(argv[1]);
    int n=0,m=0;f>>n>>m;if(n<=0||m<=0)throw std::runtime_error("shape");
    std::vector<double> lo(n),hi(n);std::vector<bool> eliminated(n);
    for(int j=0;j<n;++j){int e;f>>lo[j]>>hi[j]>>e;eliminated[j]=e!=0;}
    std::vector<ebrp::ObjectiveResourceRow> rows(m);
    for(auto& row:rows){int nz;row.scope="fixture";f>>nz>>row.rhs>>row.multiplier;
        for(int k=0;k<nz;++k){int j;double v;f>>j>>v;row.indices.push_back(j);row.coefficients.push_back(v);}}
    if(!f)throw std::runtime_error("input");
    const auto p=ebrp::projectObjectiveResources(rows,lo,hi,eliminated);
    std::cout<<std::setprecision(17)<<"{\"rhs\":"<<p.rhs<<",\"compensation_upper\":"<<p.compensation_upper<<",\"terms\":{";
    for(std::size_t k=0;k<p.indices.size();++k){if(k)std::cout<<',';std::cout<<'"'<<p.indices[k]<<"\":"<<p.coefficients[k];}
    std::cout<<"}}\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
