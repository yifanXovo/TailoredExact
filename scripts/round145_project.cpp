// Directed projection and joint-writer driver; no commercial Native loading.
#include "Round145Research.hpp"
#include <fstream>
#include <iostream>
#include <iomanip>
int main(int argc,char** argv){try{
    if(argc!=4)throw std::runtime_error("mode, input and evidence required");std::ifstream f(argv[2]);
    if(std::string(argv[1])=="block"){
        int n;long long bm,b;f>>n>>bm>>b;std::vector<std::vector<int>> s(n+1);std::vector<double> c(n+1);
        for(int i=1;i<=n;++i){int m;f>>c[i]>>m;s[i].resize(m);for(int& y:s[i])f>>y;}
        if(!f)throw std::runtime_error("block input");
        const auto r=ebrp::round145_detail::augment(ebrp::round143_detail::block(s,c,bm,b),s,c,bm,b);
        std::ofstream out(argv[3]);out<<std::setprecision(17)<<"{\"applicable\":"<<(r.applicable?"true":"false")<<",\"rows\":[";
        bool first=true;for(const auto& row:r.rows){if(!first)out<<',';first=false;
            out<<"{\"name\":"<<std::quoted(row.name)<<",\"sense\":"<<std::quoted(std::string(1,row.sense))<<",\"rhs\":"<<row.rhs<<",\"terms\":{";
            bool t=true;for(const auto& term:row.coefficients)if(term.second){if(!t)out<<',';t=false;out<<std::quoted(term.first)<<':'<<term.second;}out<<"}}";
        }out<<"],\"columns\":{";first=true;for(const auto& v:r.columns){if(!first)out<<',';first=false;out<<std::quoted(v.first)<<":["<<v.second.first<<','<<v.second.second<<']';}out<<"}}\n";
        if(!out)throw std::runtime_error("block output");return 0;
    }
    if(std::string(argv[1])!="project")throw std::runtime_error("mode");
    int n=0,m=0;f>>n>>m;if(n<=0||m<=0)throw std::runtime_error("shape");
    ebrp::FixedIntervalMipOutcome out;out.lp_primal_dual_evidence_available=out.lp_constraint_evidence_available=true;out.lp_objective_sense=1;
    ebrp::round143_detail::Block source;
    for(int j=0;j<n;++j){ebrp::FixedIntervalLpVariableEvidence v;
        f>>v.name>>v.lower_bound>>v.upper_bound>>v.primal_value>>v.reduced_cost>>v.variable_basis_status;
        out.lp_primal_dual_variable_evidence.push_back(v);
        if(v.name.rfind("rn_",0)==0)source.columns[v.name]={v.lower_bound,v.upper_bound};}
    for(int k=0;k<m;++k){int nz;ebrp::round143_detail::Row row;ebrp::FixedIntervalLpConstraintEvidence c;
        f>>row.name>>row.sense>>row.rhs>>c.dual_multiplier>>c.constraint_basis_status>>nz;c.name=row.name;
        for(int t=0;t<nz;++t){int j;double v;f>>j>>v;row.coefficients[out.lp_primal_dual_variable_evidence.at(j).name]=v;}
        source.rows.push_back(row);out.lp_primal_dual_constraint_evidence.push_back(c);}
    if(!f)throw std::runtime_error("input");
    ebrp::round144().source_sha="fixture";ebrp::round144().enabled=true;
    ebrp::round144_detail::project(source,out,argv[3],"r145_PC",true);
    const auto p=ebrp::round144().row;
    ebrp::round144ResetRun();if(!ebrp::round144().enabled||ebrp::round144().ready||ebrp::round144().attempted||!ebrp::round144().source_sha.empty())throw std::runtime_error("run reset");
    std::cout<<std::setprecision(17)<<"{\"rhs\":"<<p.rhs<<",\"terms\":{";bool first=true;
    for(const auto& term:p.coefficients){if(!first)std::cout<<',';first=false;std::cout<<std::quoted(term.first)<<':'<<term.second;}
    std::cout<<"},\"reset_test\":true}\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
