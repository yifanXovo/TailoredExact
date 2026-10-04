#include "FleetEventCuts.hpp"
#include "Parser.hpp"
#include <fstream>
#include <iomanip>
#include <iostream>
int main(int argc,char** argv){try {
    if(argc!=8)throw std::runtime_error("input T pickup drop matrix point output");
    auto in=ebrp::parseInstanceFile(argv[1],std::stod(argv[2]),std::stod(argv[3]),std::stod(argv[4]));
    std::ifstream f(argv[5]);int n,R;f>>n>>R;ebrp::NativeOtB1LinearModel m;
    if(n<1||R<1)throw std::runtime_error("matrix header");
    for(int j=0;j<n;++j){std::string name;char t;double l,u;f>>name>>t>>l>>u;m.names.push_back(name);m.types.push_back(t);m.lower_bounds.push_back(l);m.upper_bounds.push_back(u);}
    m.row_starts.push_back(0);for(int r=0;r<R;++r){char sense;double rhs;int count;f>>sense>>rhs>>count;m.senses.push_back(sense);m.rhs.push_back(rhs);
        for(int t=0;t<count;++t){int j;double a;f>>j>>a;m.column_indices.push_back(j);m.coefficients.push_back(a);}m.row_starts.push_back(static_cast<int>(m.coefficients.size()));}
    if(!f)throw std::runtime_error("matrix parse");auto c=ebrp::prepareFleetContract(in,m);
    std::ofstream out(argv[7]);out<<std::setprecision(17)<<"{\"valid\":"<<(c.valid?"true":"false")<<",\"reason\":"<<std::quoted(c.reason)<<",\"contract\":"<<ebrp::fleetContractJson(c);
    if(c.valid){std::ifstream p(argv[6]);std::vector<double> point(n);for(double& v:point)p>>v;if(!p)throw std::runtime_error("point parse");
        ebrp::FleetStatistics stats;auto rows=ebrp::separateFleetEvents(c,point,1e-5,stats,8);
        out<<",\"candidates\":"<<stats.candidates<<",\"proofs\":"<<stats.proofs<<",\"reliable\":"<<stats.reliable<<",\"rows\":[";
        for(std::size_t j=0;j<rows.size();++j){if(j)out<<',';const auto& row=rows[j];out<<"{\"activity_lower\":"<<row.activity_lower<<",\"violation_lower\":"<<row.violation_lower<<",\"proof\":"<<ebrp::fleetProofJson(row.proof)<<",\"columns\":[";
            for(std::size_t k=0;k<row.indices.size();++k){if(k)out<<',';out<<row.indices[k];}out<<"]}";}out<<']';
    }out<<"}\n";if(!out)throw std::runtime_error("output write");return c.valid?0:2;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
