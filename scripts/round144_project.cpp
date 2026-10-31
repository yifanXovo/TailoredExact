// Small independent-input driver for exact Fraction vs production intervals.
#include "Round144Research.hpp"
#include <fstream>
#include <iostream>
#include <iomanip>
int main(int argc,char** argv){try{
    if(argc!=3)throw std::runtime_error("input and evidence output required");std::ifstream f(argv[1]);
    int n=0,m=0;f>>n>>m;if(n<=0||m<=0)throw std::runtime_error("shape");
    ebrp::FixedIntervalMipOutcome out;out.lp_primal_dual_evidence_available=out.lp_constraint_evidence_available=true;out.lp_objective_sense=1;
    ebrp::round143_detail::Block rn;
    for(int j=0;j<n;++j){ebrp::FixedIntervalLpVariableEvidence v;
        f>>v.name>>v.lower_bound>>v.upper_bound>>v.primal_value>>v.reduced_cost>>v.variable_basis_status;
        out.lp_primal_dual_variable_evidence.push_back(v);
        if(v.name.rfind("rn_",0)==0)rn.columns[v.name]={v.lower_bound,v.upper_bound};}
    for(int k=0;k<m;++k){int nz;ebrp::round143_detail::Row row;ebrp::FixedIntervalLpConstraintEvidence c;
        f>>row.name>>row.sense>>row.rhs>>c.dual_multiplier>>c.constraint_basis_status>>nz;c.name=row.name;
        for(int t=0;t<nz;++t){int j;double v;f>>j>>v;row.coefficients[out.lp_primal_dual_variable_evidence.at(j).name]=v;}
        rn.rows.push_back(row);out.lp_primal_dual_constraint_evidence.push_back(c);}
    if(!f)throw std::runtime_error("input");
    ebrp::round144().source_sha="fixture";ebrp::round144().enabled=true;
    ebrp::round144_detail::project(rn,out,argv[2]);
    const auto p=ebrp::round144().row;
    ebrp::round144ResetRun();if(!ebrp::round144().enabled||ebrp::round144().ready||ebrp::round144().attempted||!ebrp::round144().source_sha.empty())throw std::runtime_error("run reset");
    std::cout<<std::setprecision(17)<<"{\"rhs\":"<<p.rhs<<",\"terms\":{";bool first=true;
    for(const auto& term:p.coefficients){if(!first)std::cout<<',';first=false;std::cout<<std::quoted(term.first)<<':'<<term.second;}
    std::cout<<"},\"reset_test\":true}\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
