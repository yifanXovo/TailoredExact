#pragma once
#include "Round148Research.hpp"

namespace ebrp {
namespace round149_detail {
inline void require(bool ok,const std::string& why){if(!ok)throw std::runtime_error("round149_"+why);}
using Interval=round148_detail::Interval;
using round148_detail::val;
using round148_detail::add;
using round148_detail::sub;
using round148_detail::mul;
using round148_detail::div;
inline Interval absolute(Interval x){
    return {x.lo<=0&&x.hi>=0?0.:std::min(std::fabs(x.lo),std::fabs(x.hi)),
            std::max(std::fabs(x.lo),std::fabs(x.hi))};
}
struct Floor {
    bool feasible=true;
    double lower=0,dual_lower=0,mu=0,nu=0,primal=0,seconds=0;
    std::vector<double> inventory;
};
// A greedy allocation only selects an actual finite nonnegative multiplier.
// Validity uses weak duality and outward arithmetic at that fixed multiplier;
// neither approximate sorting nor the approximate primal is a certificate.
inline Floor floor(const std::vector<std::vector<int>>& support,
                   const std::vector<double>& c,const std::vector<double>& w,
                   long long bm,long long b){
    const auto tick=std::chrono::steady_clock::now();Floor out;
    const int n=int(support.size())-1;
    require(n>0&&c.size()==support.size()&&w.size()==support.size()&&0<=bm&&bm<=b&&b<=9007199254740992LL,"floor_shape");
    long long minsum=0,maxsum=0;double sum=0;
    std::vector<int> order;out.inventory.resize(n+1);
    for(int i=1;i<=n;++i){
        require(!support[i].empty()&&support[i].front()>=0,"floor_support");
        require(std::is_sorted(support[i].begin(),support[i].end()),"floor_support_order");
        require(std::isfinite(c[i])&&c[i]>0&&std::isfinite(w[i])&&w[i]>=0,"floor_coefficients");
        minsum+=support[i].front();maxsum+=support[i].back();
        out.inventory[i]=std::max(double(support[i].front()),std::min(double(support[i].back()),1./c[i]));
        sum+=out.inventory[i];order.push_back(i);
    }
    if(minsum>b||maxsum<bm){out.feasible=false;return out;}
    std::sort(order.begin(),order.end(),[&](int i,int j){
        const double a=w[i]*c[i],z=w[j]*c[j];return a<z||(a==z&&i<j);
    });
    const bool decrease=sum>b,increase=sum<bm;
    double remaining=decrease?sum-b:increase?bm-sum:0.;
    for(int i:order){
        if(remaining<=0)break;
        const double capacity=decrease?out.inventory[i]-support[i].front():support[i].back()-out.inventory[i];
        const double take=std::min(remaining,capacity);if(take<=0)continue;
        out.inventory[i]+=decrease?-take:take;remaining-=take;
        const double marginal=w[i]*c[i];require(std::isfinite(marginal),"finite_multiplier");
        if(decrease)out.nu=marginal;else out.mu=marginal;
    }
    const auto slope=sub(val(out.nu),val(out.mu));
    auto dual=sub(mul(val(out.mu),val(double(bm))),mul(val(out.nu),val(double(b))));
    for(int i=1;i<=n;++i){
        const auto endpoint=[&](double y){
            return add(mul(val(w[i]),absolute(sub(mul(val(c[i]),val(y)),val(1)))),mul(slope,val(y)));
        };
        double lower=std::min(endpoint(support[i].front()).lo,endpoint(support[i].back()).lo);
        const auto kink=div(val(1),val(c[i]));
        // The exact kink is inside its enclosure. Including a possibly extra
        // candidate weakens the minimum and is safe at a box boundary.
        if(kink.lo<=support[i].back()&&kink.hi>=support[i].front())
            lower=std::min(lower,mul(slope,kink).lo);
        dual=add(dual,val(lower));
        out.primal+=w[i]*std::fabs(c[i]*out.inventory[i]-1.);
    }
    out.dual_lower=dual.lo;out.lower=std::max(0.,dual.lo);
    out.seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-tick).count();return out;
}
inline std::vector<round143_detail::Row> rows(const std::vector<std::vector<int>>& support,double beta,double old_upper){
    std::vector<round143_detail::Row> result;
    require(std::isfinite(beta)&&beta>=0&&std::isfinite(old_upper),"row_upper");
    // Omitting the entire row preserves validity if Native would remove a
    // tiny negative selector coefficient. Never round beta down.
    if(beta>=old_upper||beta<1e-12)return result;
    for(std::size_t i=1;i<support.size();++i)for(int y:support[i]){
        const auto suffix=std::to_string(i)+"_"+std::to_string(y);
        result.push_back({"r149_PF_"+suffix,{{"state_g_"+suffix,1.},{"state_"+suffix,-beta}},'<',0});
    }
    return result;
}
}
struct Round149Controls {
    bool enabled=false,generated=false;
    std::string input_sha;
    long long bm=0,b=0;
    double gamma_L=0,gamma_U=0,cutoff=0,beta=0;
    std::vector<std::vector<int>> support;
    std::vector<double> ratios,weights;
    round149_detail::Floor floor;
    std::map<std::string,std::vector<round143_detail::Row>> expected;
};
inline Round149Controls& round149(){static Round149Controls c;return c;}
inline void round149ResetRun(){const bool enabled=round149().enabled;round149()=Round149Controls{};round149().enabled=enabled;}
namespace round149_detail {
inline CanonicalCompactModelArtifact embed(const Instance& instance,const CanonicalCompactModelArtifact& base,
                                          double cutoff,const std::filesystem::path& path){
    auto& c=round149();if(!c.enabled)return base;
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
        const double actual=hit==objective.coefficients.end()?0.:hit->second;
        require(std::isfinite(actual)&&actual>=0&&ratios[i]>=1e-12,"actual_coefficients");
        weights[i]=actual<1e-12?0.:actual;
    }
    for(int capacity:instance.Q)q+=capacity;const long long bm=std::max(0LL,b-q);
    const auto input_sha=fileSha256(instance.path);
    if(!c.generated){
        c.input_sha=input_sha;c.bm=bm;c.b=b;c.ratios=ratios;c.weights=weights;c.support=support;
        c.gamma_L=base.gamma_L;c.gamma_U=base.gamma_U;c.cutoff=cutoff;
        c.floor=floor(support,ratios,weights,bm,b);
        c.beta=std::min(c.gamma_U,sub(val(cutoff),val(c.floor.lower)).hi);
        require(c.beta>=0,"negative_beta_scope_or_arithmetic");c.generated=true;
        std::ofstream f(path.parent_path()/"round149_root.json");f<<std::setprecision(17)
            <<"{\"input_SHA\":"<<std::quoted(input_sha)<<",\"base_model_SHA\":"<<std::quoted(base.sha256)
            <<",\"Bminus\":"<<bm<<",\"B\":"<<b<<",\"gamma_L\":"<<c.gamma_L<<",\"gamma_U\":"<<c.gamma_U
            <<",\"own_cutoff\":"<<cutoff<<",\"penalty_lower\":"<<c.floor.lower<<",\"beta\":"<<c.beta
            <<",\"dual_lower\":"<<c.floor.dual_lower<<",\"mu\":"<<c.floor.mu<<",\"nu\":"<<c.floor.nu
            <<",\"primal_diagnostic\":"<<c.floor.primal<<",\"feasible_resource_box\":"<<(c.floor.feasible?"true":"false")
            <<",\"arithmetic_seconds\":"<<c.floor.seconds<<",\"stations\":[";
        for(int i=1;i<=instance.V;++i){if(i>1)f<<',';
            f<<"{\"i\":"<<i<<",\"c\":"<<ratios[i]<<",\"omega\":"<<weights[i]
                <<",\"lo\":"<<support[i].front()<<",\"hi\":"<<support[i].back()<<'}';}
        f<<"],\"root_beta_frozen\":true,\"proof_root_unchanged\":true,\"source_solves\":0,\"extra_root_LP\":0,\"new_columns\":0}\n";
        f.close();require(bool(f),"root_evidence_write");
    }
    require(c.input_sha==input_sha&&c.ratios==ratios&&c.weights==weights&&c.bm==bm&&c.b==b&&
            base.gamma_L>=c.gamma_L&&base.gamma_U<=c.gamma_U&&cutoff<=c.cutoff,"embedding_scope");
    for(int i=1;i<=instance.V;++i)
        require(std::includes(c.support[i].begin(),c.support[i].end(),support[i].begin(),support[i].end()),"support_expanded");
    auto added=c.floor.feasible&&c.floor.lower>0?rows(support,c.beta,base.gamma_U):std::vector<round143_detail::Row>{};
    const auto gd=round146().expected.find(base.sha256);require(gd!=round146().expected.end(),"GD_expected_base_missing");
    auto out=base;
    if(!added.empty()){
        out=round144_detail::append(base,added,{},path,"PF");
        out.model_scope=base.model_scope+"_round149_PF";
        out.row_signature=base.row_signature+"|round149:"+out.sha256;
    }
    round146().expected.emplace(out.sha256,gd->second);c.expected.emplace(out.sha256,added);
    std::ofstream f(path.string()+".round149.json");f<<std::setprecision(17)
        <<"{\"base_SHA\":"<<std::quoted(base.sha256)<<",\"final_SHA\":"<<std::quoted(out.sha256)
        <<",\"cutoff\":"<<cutoff<<",\"gamma_L\":"<<base.gamma_L<<",\"gamma_U\":"<<base.gamma_U
        <<",\"beta\":"<<c.beta<<",\"added_rows\":"<<added.size()<<",\"added_nonzeros\":"<<2*added.size()
        <<",\"GD_expected_rows\":"<<gd->second.size()<<",\"compatible_domain\":true,\"first_solve_before_append\":false}\n";
    f.close();require(bool(f),"embedding_evidence_write");return out;
}
}
}
