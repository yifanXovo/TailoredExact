#pragma once
#include "Round143Research.hpp"
#include "Round141Research.hpp"
#include "FixedIntervalMipBackend.hpp"
#include "ObjectiveResourceCompression.hpp"

namespace ebrp {
struct Round144Controls {
    bool enabled=false,attempted=false,ready=false,source_running=false;
    std::string input_sha,source_sha;double lower=0,upper=0,cutoff=0;
    std::vector<std::vector<int>> support;
    round143_detail::Row row;
    std::map<std::string,round143_detail::Row> expected;
};
inline Round144Controls& round144(){static Round144Controls c;return c;}
inline void round144ResetRun(){const bool enabled=round144().enabled;round144()=Round144Controls{};round144().enabled=enabled;}
namespace round144_detail {
inline void require(bool ok,const std::string& why){if(!ok)throw std::runtime_error("round144_"+why);}
inline CanonicalCompactModelArtifact append(const CanonicalCompactModelArtifact& base,
    const std::vector<round143_detail::Row>& rows,const std::map<std::string,std::pair<double,double>>& columns,
    const std::filesystem::path& path,const std::string& scope){
    require(base.written&&fileSha256(base.path)==base.sha256&&!std::filesystem::exists(path),"append_identity_or_collision");
    auto text=round141_detail::material(base.path);auto pos=text.find("Bounds\n");require(pos!=std::string::npos,"bounds_missing");
    std::string addition;long long nz=0;
    for(const auto& row:rows){addition+=round143_detail::emit(row);for(const auto& term:row.coefficients)nz+=term.second!=0;}
    text.insert(pos,addition);std::ostringstream bounds;bounds<<std::setprecision(17);
    for(const auto& c:columns)bounds<<' '<<c.second.first<<" <= "<<c.first<<" <= "<<c.second.second<<'\n';
    text.insert(text.find("Bounds\n")+7,bounds.str());
    std::ofstream f(path,std::ios::binary);f<<text;f.close();require(bool(f),"append_write");
    auto out=base;out.path=path;out.sha256=fileSha256(path);out.row_signature+="|round144:"+out.sha256;
    out.model_scope+="_round144_"+scope;out.rows+=rows.size();out.columns+=columns.size();out.nonzeros+=nz;return out;
}
inline round143_detail::Block block(const Instance& instance,const CanonicalCompactModelArtifact& base){
    auto& c=round144();c.input_sha=fileSha256(instance.path);c.lower=base.gamma_L;c.upper=base.gamma_U;
    c.support=round141_detail::supports(round141_detail::material(base.path),instance.V);
    long long B=0,Q=0;std::vector<double> ratios(instance.V+1);
    for(int i=1;i<=instance.V;++i){B+=instance.initial[i];ratios[i]=1./instance.target[i];}
    for(int q:instance.Q)Q+=q;
    return round143_detail::block(c.support,ratios,std::max(0LL,B-Q),B);
}
inline void project(const round143_detail::Block& rn,const FixedIntervalMipOutcome& out,
    const std::filesystem::path& path,const std::string& row_name="r144_PC",bool allow_inventory=false){
    require(out.lp_primal_dual_evidence_available&&out.lp_constraint_evidence_available&&out.lp_objective_sense==1,"source_dual_unavailable");
    std::map<std::string,int> index;std::vector<double> lower,upper;std::vector<bool> eliminate;
    for(const auto& v:out.lp_primal_dual_variable_evidence){
        require(index.emplace(v.name,int(index.size())).second,"duplicate_variable");
        lower.push_back(v.lower_bound);upper.push_back(v.upper_bound);eliminate.push_back(v.name.rfind("rn_",0)==0);
        const auto it=rn.columns.find(v.name);
        if(eliminate.back())require(it!=rn.columns.end()&&it->second==std::make_pair(v.lower_bound,v.upper_bound),"actual_extension_bounds");
    }
    require(std::count(eliminate.begin(),eliminate.end(),true)==static_cast<long long>(rn.columns.size()),"extension_columns_missing");
    std::map<std::string,double> pi;for(const auto& r:out.lp_primal_dual_constraint_evidence)require(pi.emplace(r.name,r.dual_multiplier).second,"duplicate_constraint");
    std::vector<ObjectiveResourceRow> rows;int repairs=0;
    for(const auto& r:rn.rows){auto it=pi.find(r.name);require(it!=pi.end()&&std::isfinite(it->second),"RN_Pi_missing");
        const double raw=it->second;double multiplier=raw;
        if(r.sense=='>')multiplier=std::max(0.,raw);
        else if(r.sense=='<')multiplier=std::min(0.,raw);
        else require(r.sense=='=',"row_sense");
        repairs+=raw!=multiplier;
        // All normalized source rows use <= with a nonnegative multiplier.
        const double sign=multiplier<0?1.:-1.;
        ObjectiveResourceRow row;row.scope=round144().source_sha;row.vehicle=0;
        row.multiplier=std::fabs(multiplier);row.rhs=sign*r.rhs;
        for(const auto& term:r.coefficients){require(index.count(term.first),"source_column_missing");row.indices.push_back(index.at(term.first));row.coefficients.push_back(sign*term.second);}
        rows.push_back(std::move(row));
    }
    const auto compressed=projectObjectiveResources(rows,lower,upper,eliminate);
    auto& c=round144();c.row.name=row_name;c.row.sense='<';c.row.rhs=compressed.rhs;
    for(std::size_t k=0;k<compressed.indices.size();++k){const auto& name=out.lp_primal_dual_variable_evidence.at(compressed.indices[k]).name;
        require(name=="G"||name.rfind("state_",0)==0||(allow_inventory&&name.rfind("Y_",0)==0),"projected_nonoriginal_column");c.row.coefficients[name]=compressed.coefficients[k];}
    // An optimal RN block may have zero dual weight. Its 0<=0 projection
    // contains no new information and is omitted uniformly as redundant.
    require(!c.row.coefficients.empty()||c.row.rhs>=0,"empty_projection_infeasible");
    std::ofstream f(path);f<<std::setprecision(17)<<"{\"source_SHA\":"<<std::quoted(c.source_sha)<<",\"sign_repairs\":"<<repairs
        <<",\"compensation_upper\":"<<compressed.compensation_upper<<",\"source_rows\":[";
    bool first_source=true;for(const auto& r:rn.rows){if(!first_source)f<<',';first_source=false;f<<std::quoted(r.name);}
    f<<"],\"row\":{\"name\":"<<std::quoted(row_name)<<",\"sense\":\"<\",\"rhs\":"<<c.row.rhs<<",\"terms\":{";
    bool first=true;for(const auto& term:c.row.coefficients){if(!first)f<<',';first=false;f<<std::quoted(term.first)<<':'<<term.second;}f<<"}},\"variables\":[";
    first=true;for(const auto& v:out.lp_primal_dual_variable_evidence){if(!first)f<<',';first=false;
        f<<"{\"name\":"<<std::quoted(v.name)<<",\"LB\":"<<v.lower_bound<<",\"UB\":"<<v.upper_bound<<",\"X\":"<<v.primal_value
         <<",\"RC\":"<<v.reduced_cost<<",\"VBasis\":"<<v.variable_basis_status<<'}';}f<<"],\"constraints\":[";
    first=true;for(const auto& r:out.lp_primal_dual_constraint_evidence){if(!first)f<<',';first=false;
        f<<"{\"name\":"<<std::quoted(r.name)<<",\"Pi\":"<<r.dual_multiplier<<",\"Slack\":"<<r.slack<<",\"CBasis\":"<<r.constraint_basis_status<<'}';}
    f<<"],\"RN_columns_submitted\":0,\"arithmetic\":\"outward binary64 intervals; signed finite-box conversion and elimination\"}\n";
    f.close();require(bool(f),"projection_evidence_write");c.ready=!c.row.coefficients.empty();
}
inline CanonicalCompactModelArtifact embed(const Instance& instance,const CanonicalCompactModelArtifact& base,
    double cutoff,const std::filesystem::path& path){
    auto& c=round144();require(c.ready&&c.input_sha==fileSha256(instance.path)&&base.gamma_L>=c.lower&&base.gamma_U<=c.upper&&cutoff<=c.cutoff,"embedding_scope");
    const auto support=round141_detail::supports(round141_detail::material(base.path),instance.V);
    for(int i=1;i<=instance.V;++i)require(std::includes(c.support[i].begin(),c.support[i].end(),support[i].begin(),support[i].end()),"embedding_support");
    auto row=c.row;
    // An absent root selector in a narrower support is identically zero.
    for(auto it=row.coefficients.begin();it!=row.coefficients.end();){
        if(it->first=="G"||it->first.rfind("Y_",0)==0){++it;continue;}
        const auto parts=round141_detail::split(it->first,'_');require(parts.size()==3,"selector_name");
        int i=std::stoi(parts[1]),y=std::stoi(parts[2]);
        if(!std::binary_search(support.at(i).begin(),support.at(i).end(),y))it=row.coefficients.erase(it);else ++it;
    }
    const auto out=append(base,{row},{},path,"compact");c.expected.emplace(out.sha256,std::move(row));return out;
}
}
}
