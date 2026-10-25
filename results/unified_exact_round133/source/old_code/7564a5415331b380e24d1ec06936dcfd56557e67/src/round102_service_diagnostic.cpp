#include "ServiceResourceCuts.hpp"
#include "Parser.hpp"
#include <fstream>
#include <iomanip>
#include <iostream>
#include <chrono>
int main(int argc,char**argv){try{
    if(argc!=8)throw std::runtime_error("input T pickup drop matrix point output");
    auto in=ebrp::parseInstanceFile(argv[1],std::stod(argv[2]),std::stod(argv[3]),std::stod(argv[4]));
    std::ifstream f(argv[5]);int n,R;f>>n>>R;ebrp::NativeOtB1LinearModel m;
    if(n<1||R<1)throw std::runtime_error("matrix header");
    for(int j=0;j<n;++j){std::string name;char t;double l,u;f>>name>>t>>l>>u;m.names.push_back(name);m.types.push_back(t);m.lower_bounds.push_back(l);m.upper_bounds.push_back(u);}
    m.row_starts.push_back(0);for(int r=0;r<R;++r){char sense;double rhs;int count;f>>sense>>rhs>>count;m.senses.push_back(sense);m.rhs.push_back(rhs);
        for(int t=0;t<count;++t){int j;double a;f>>j>>a;m.column_indices.push_back(j);m.coefficients.push_back(a);}m.row_starts.push_back(static_cast<int>(m.coefficients.size()));}
    if(!f)throw std::runtime_error("matrix parse");
    auto c=ebrp::prepareServiceContract(in,m);if(!c.valid)throw std::runtime_error(c.reason);
    std::ifstream p(argv[6]);std::vector<double> point(n);for(auto&v:point)p>>v;if(!p)throw std::runtime_error("point parse");
    ebrp::ServiceStatistics stats;auto tick=std::chrono::steady_clock::now();auto rows=ebrp::separateServiceResources(c,point,1e-5,stats);
    const double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-tick).count();
    std::ofstream out(argv[7]);out<<std::setprecision(17)<<"{\"valid\":true,\"seconds\":"<<sec<<",\"contract\":"<<ebrp::serviceContractJson(c)<<",\"directions\":"<<stats.directions<<",\"dp_calls\":"<<stats.dp_calls<<",\"rows\":[";
    for(std::size_t j=0;j<rows.size();++j){if(j)out<<',';auto&r=rows[j];out<<"{\"rhs\":"<<r.rhs<<",\"activity_lower\":"<<r.activity_lower<<",\"violation_lower\":"<<r.violation_lower<<",\"proofs\":[";
        for(std::size_t k=0;k<r.proofs.size();++k){if(k)out<<',';out<<ebrp::serviceSupportJson(r.proofs[k]);}out<<"],\"columns\":[";
        for(std::size_t t=0;t<r.indices.size();++t){if(t)out<<',';out<<'['<<r.indices[t]<<','<<r.coefficients[t]<<','<<point[r.indices[t]]<<']';}out<<"]}";
    }out<<"]}\n";out.flush();out.close();if(!out)throw std::runtime_error("output close");return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
