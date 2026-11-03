#pragma once
#include "Round149Research.hpp"
#include "Round138Research.hpp"

namespace ebrp {
namespace round151_detail {
inline void require(bool ok,const std::string& why){if(!ok)throw std::runtime_error("round151_"+why);}
using round149_detail::val;
using round149_detail::add;
using round149_detail::sub;
using round149_detail::mul;
using round149_detail::div;
using round149_detail::absolute;
// Monotone upward transport, shared by P and C. Zero is an exact one-term row.
inline double transport(double x){
    require(std::isfinite(x),"finite_cap");
    return x!=0&&std::fabs(x)<1e-12?(x<0?0.:1e-12):x;
}
struct State {int i=0,y=0;double dual_lower=0,penalty_lower=0,beta=0;};
struct Caps {
    round149_detail::Floor floor;
    double beta0=0,seconds=0;
    std::vector<State> states;
};
inline Caps caps(const std::vector<std::vector<int>>& support,const std::vector<double>& c,
                 const std::vector<double>& w,long long bm,long long b,double cutoff,double upper){
    const auto tick=std::chrono::steady_clock::now();Caps out;
    out.floor=round149_detail::floor(support,c,w,bm,b);
    out.beta0=std::min(upper,sub(val(cutoff),val(out.floor.lower)).hi);
    if(out.floor.feasible){
        const int n=int(support.size())-1;
        const auto slope=sub(val(out.floor.nu),val(out.floor.mu));
        const auto resource=sub(mul(val(out.floor.mu),val(double(bm))),mul(val(out.floor.nu),val(double(b))));
        std::vector<double> minima(n+1);
        std::vector<round149_detail::Interval> prefix(n+2),suffix(n+2);
        const auto cost=[&](int i,double y){
            return add(mul(val(w[i]),absolute(sub(mul(val(c[i]),val(y)),val(1)))),mul(slope,val(y)));
        };
        for(int i=1;i<=n;++i){
            minima[i]=std::min(cost(i,support[i].front()).lo,cost(i,support[i].back()).lo);
            const auto kink=div(val(1),val(c[i]));
            if(kink.lo<=support[i].back()&&kink.hi>=support[i].front())
                minima[i]=std::min(minima[i],mul(slope,kink).lo);
            prefix[i]=add(prefix[i-1],val(minima[i]));
        }
        for(int i=n;i>=1;--i)suffix[i]=add(val(minima[i]),suffix[i+1]);
        for(int i=1;i<=n;++i){
            // Never subtract an independently rounded local lower bound.
            const auto leave=add(add(resource,prefix[i-1]),suffix[i+1]);
            for(int y:support[i]){
                const double diy=add(leave,cost(i,y)).lo;
                const double p=std::max(out.floor.lower,std::max(0.,diy));
                out.states.push_back({i,y,diy,p,std::min(out.beta0,sub(val(cutoff),val(p)).hi)});
            }
        }
    }
    out.seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-tick).count();return out;
}
inline std::vector<round143_detail::Row> rows(const Caps& root,const std::vector<std::vector<int>>& support,
                                            double upper,const std::string& mode){
    require(mode=="uniform"||mode=="conditional","row_mode");
    std::vector<round143_detail::Row> result;
    if(!root.floor.feasible)return result;
    for(const auto& s:root.states){
        if(!std::binary_search(support.at(s.i).begin(),support.at(s.i).end(),s.y))continue;
        const double beta=transport(mode=="uniform"?root.beta0:s.beta);
        require(beta<=transport(root.beta0),"actual_C_subset_P");
        if(beta>=upper)continue; // Per-state child dominance, including floor=0.
        const auto suffix=std::to_string(s.i)+"_"+std::to_string(s.y);
        round143_detail::Row row{"r151_cap_"+suffix,{{"state_g_"+suffix,1.}},'<',0};
        if(beta!=0)row.coefficients["state_"+suffix]=-beta;
        result.push_back(std::move(row));
    }
    return result;
}
inline void dump(std::ostream& f,const Caps& a){
    f<<std::setprecision(17)<<"\"feasible_resource_box\":"<<(a.floor.feasible?"true":"false")
        <<",\"penalty_lower\":"<<a.floor.lower<<",\"dual_lower\":"<<a.floor.dual_lower
        <<",\"mu\":"<<a.floor.mu<<",\"nu\":"<<a.floor.nu<<",\"beta0\":"<<a.beta0
        <<",\"transported_beta0\":"<<transport(a.beta0)<<",\"arithmetic_seconds\":"<<a.seconds<<",\"states\":[";
    bool first=true;for(const auto& s:a.states){if(!first)f<<',';first=false;
        f<<"{\"i\":"<<s.i<<",\"y\":"<<s.y<<",\"dual_lower\":"<<s.dual_lower
            <<",\"penalty_lower\":"<<s.penalty_lower<<",\"beta\":"<<s.beta
            <<",\"transported_beta\":"<<transport(s.beta)<<'}';}f<<']';
}
}
struct Round151Controls {
    std::string mode="off",input_sha;
    bool generated=false;
    long long bm=0,b=0;
    double gamma_L=0,gamma_U=0,cutoff=0;
    std::vector<std::vector<int>> support;
    std::vector<double> ratios,weights;
    round151_detail::Caps caps;
    std::map<std::string,std::vector<round143_detail::Row>> expected;
};
inline Round151Controls& round151(){static Round151Controls c;return c;}
inline void round151ResetRun(){const auto mode=round151().mode;round151()=Round151Controls{};round151().mode=mode;}
namespace round151_detail {
inline CanonicalCompactModelArtifact embed(const Instance& instance,const CanonicalCompactModelArtifact& base,
                                          double cutoff,const std::filesystem::path& path){
    auto& c=round151();if(c.mode=="off")return base;
    require(!round146().enabled&&!round149().enabled&&!round148().enabled&&!round138().stock_rlt,"B_GDoff_contract");
    require(base.written&&fileSha256(base.path)==base.sha256&&std::isfinite(cutoff),"base_identity");
    const auto text=round141_detail::material(base.path);
    const auto support=round141_detail::supports(text,instance.V);
    const auto objective=round141_detail::objective(text);
    require(objective.constant==0&&objective.coefficients.at("G")==1,"objective_units");
    std::vector<double> ratios(instance.V+1),weights(instance.V+1);
    for(const auto& term:objective.coefficients)
        require(term.first=="G"||(term.first.rfind("e_",0)==0&&term.second>=0),"objective_scope");
    long long b=0,q=0;
    for(int i=1;i<=instance.V;++i){
        b+=instance.initial[i];ratios[i]=1./instance.target[i];
        const auto hit=objective.coefficients.find("e_"+std::to_string(i));
        weights[i]=hit==objective.coefficients.end()?0.:hit->second;
        require(std::isfinite(weights[i])&&weights[i]>=0&&ratios[i]>=1e-12,"actual_coefficients");
    }
    for(int capacity:instance.Q)q+=capacity;const long long bm=std::max(0LL,b-q);
    const auto input_sha=fileSha256(instance.path);
    if(!c.generated){
        c.input_sha=input_sha;c.bm=bm;c.b=b;c.ratios=ratios;c.weights=weights;c.support=support;
        c.gamma_L=base.gamma_L;c.gamma_U=base.gamma_U;c.cutoff=cutoff;
        c.caps=caps(support,ratios,weights,bm,b,cutoff,base.gamma_U);c.generated=true;
        std::ofstream f(path.parent_path()/"round151_root.json");f<<std::setprecision(17)
            <<"{\"input_SHA\":"<<std::quoted(input_sha)<<",\"base_model_SHA\":"<<std::quoted(base.sha256)
            <<",\"mode\":"<<std::quoted(c.mode)<<",\"Bminus\":"<<bm<<",\"B\":"<<b
            <<",\"gamma_L\":"<<c.gamma_L<<",\"gamma_U\":"<<c.gamma_U<<",\"own_cutoff\":"<<cutoff<<',';
        dump(f,c.caps);f<<",\"root_caps_frozen\":true,\"proof_root_unchanged\":true,\"GD\":false,\"source_solves\":0,\"extra_root_LP\":0,\"new_columns\":0}\n";
        f.close();require(bool(f),"root_evidence_write");
    }
    require(c.input_sha==input_sha&&c.ratios==ratios&&c.weights==weights&&c.bm==bm&&c.b==b&&
        base.gamma_L>=c.gamma_L&&base.gamma_U<=c.gamma_U&&cutoff<=c.cutoff,"embedding_scope");
    for(int i=1;i<=instance.V;++i)
        require(std::includes(c.support[i].begin(),c.support[i].end(),support[i].begin(),support[i].end()),"support_expanded");
    const auto added=rows(c.caps,support,base.gamma_U,c.mode);auto out=base;
    if(!added.empty()){
        out=round144_detail::append(base,added,{},path,"R151");
        out.model_scope=base.model_scope+"_round151_"+c.mode;
        out.row_signature=base.row_signature+"|round151:"+out.sha256;
    }
    c.expected.emplace(out.sha256,added);
    long long nz=0;for(const auto& row:added)nz+=row.coefficients.size();
    std::ofstream f(path.string()+".round151.json");f<<std::setprecision(17)
        <<"{\"base_SHA\":"<<std::quoted(base.sha256)<<",\"final_SHA\":"<<std::quoted(out.sha256)
        <<",\"mode\":"<<std::quoted(c.mode)<<",\"cutoff\":"<<cutoff<<",\"gamma_L\":"<<base.gamma_L
        <<",\"gamma_U\":"<<base.gamma_U<<",\"added_rows\":"<<added.size()<<",\"added_nonzeros\":"<<nz
        <<",\"compatible_domain\":true,\"first_solve_before_append\":false,\"GD\":false}\n";
    f.close();require(bool(f),"embedding_evidence_write");return out;
}
}
}
