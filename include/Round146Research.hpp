#pragma once
#include "Round144Research.hpp"
#include <chrono>

namespace ebrp {
namespace round146_detail {
inline void require(bool ok,const std::string& why){if(!ok)throw std::runtime_error("round146_"+why);}
struct StateBound {int i=0,y=0;bool feasible=false;double lower=0,upper=0,low=0,high=0;};
struct Block {
    bool applicable=false,infeasible=false;
    double lower=0,upper=0,seconds=0;
    std::vector<StateBound> states;
    std::vector<round143_detail::Row> rows;
};
// Continuous inventory boxes relax holes in the actual discrete support. The
// dyadic sums use the same checked exact units as R140/R143, without an LP.
inline Block block(const std::vector<std::vector<int>>& support,const std::vector<double>& c,
                   long long bm,long long b,bool conditional=true){
    using namespace round140_detail;
    const auto tick=std::chrono::steady_clock::now();Block out;const int n=int(support.size())-1;
    require(n>0&&c.size()==support.size()&&0<=bm&&bm<=b&&b<=9007199254740992LL,"scope_shape");
    int exponent=0;std::vector<int> order(n);std::vector<Int> costs(n+1);
    for(int i=1;i<=n;++i){
        require(!support[i].empty()&&support[i].front()>=0,"support");
        for(std::size_t k=1;k<support[i].size();++k)require(support[i][k]>support[i][k-1],"sorted_distinct_support");
        require(std::isfinite(c[i])&&c[i]>=0,"nonnegative_actual_ratio");
        if(c[i]>0){int e=0;std::frexp(c[i],&e);exponent=std::min(exponent,e-53);}order[i-1]=i;
    }
    for(int i=1;i<=n;++i)costs[i]=units(c[i],exponent);
    std::sort(order.begin(),order.end(),[&](int i,int j){return c[i]<c[j]||(c[i]==c[j]&&i<j);});
    const auto bounds=[&](int fixed,int value,Int& lower,Int& upper){
        long long minimum=0,maximum=0;Int initial=0;
        for(int i=1;i<=n;++i){const int lo=i==fixed?value:support[i].front(),hi=i==fixed?value:support[i].back();
            minimum+=lo;maximum+=hi;initial=add(initial,mul(costs[i],lo));}
        const long long lb=std::max(bm,minimum),ub=std::min(b,maximum);if(lb>ub)return false;
        const auto fill=[&](long long total,bool reverse){Int result=initial;long long remaining=total-minimum;
            for(int k=0;k<n;++k){const int i=order[reverse?n-1-k:k];
                const long long capacity=i==fixed?0:static_cast<long long>(support[i].back())-support[i].front();
                const long long take=std::min(remaining,capacity);result=add(result,mul(costs[i],take));remaining-=take;}
            require(remaining==0,"inventory_fill");return result;};
        lower=fill(lb,false);upper=fill(ub,true);return true;
    };
    Int lower=0,upper=0;
    if(!bounds(0,0,lower,upper)){out.infeasible=true;return out;}
    if(lower<=0)return out; // Preserve the existing all-zero Gini convention.
    out.lower=down(lower,exponent);out.upper=-down(-upper,exponent);
    require(out.lower>0&&std::isfinite(out.upper),"positive_denominator_conversion");out.applicable=true;
    round143_detail::Row low{"r146_GD_low",{{"G",double(n)}},'>',0},high{"r146_GD_high",{{"G",double(n)}},'>',0};
    const double inf=std::numeric_limits<double>::infinity();
    for(int i=1;i<=n;++i)for(int y:support[i]){
        StateBound state;state.i=i;state.y=y;Int dl=lower,du=upper;
        state.feasible=!conditional||bounds(i,y,dl,du);
        if(state.feasible){
            require(dl>=lower&&du<=upper&&dl>0&&du>=dl,"conditional_denominator_order");
            state.lower=down(dl,exponent);state.upper=-down(-du,exponent);
            const Int numerator=mul(mul(costs[i],y),n);
            if(numerator==0)state.low=1; // In particular, zero-stock coefficient is exactly one.
            else {
                const double num_lo=down(numerator,exponent),num_hi=-down(-numerator,exponent);
                const double ratio_hi=std::nextafter(num_hi/state.lower,inf);
                const double ratio_lo=std::nextafter(num_lo/state.upper,-inf);
                state.low=std::max(0.,std::nextafter(1.-ratio_hi,-inf));
                state.high=std::max(0.,std::nextafter(ratio_lo-1.,-inf));
            }
            // Omitting tiny positive selector coefficients weakens the row and
            // avoids the Native reader's tiny-coefficient removal threshold.
            if(state.low<1e-12)state.low=0;if(state.high<1e-12)state.high=0;
            if(state.low)low.coefficients[round143_detail::state(i,y)]=-state.low;
            if(state.high)high.coefficients[round143_detail::state(i,y)]=-state.high;
        }
        out.states.push_back(state);
    }
    if(low.coefficients.size()>1)out.rows.push_back(std::move(low));
    if(high.coefficients.size()>1)out.rows.push_back(std::move(high));
    out.seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-tick).count();return out;
}
}
struct Round146Controls {
    bool enabled=false,generated=false;
    std::string input_sha;
    long long bm=0,b=0;
    std::vector<std::vector<int>> support;
    std::vector<double> ratios;
    round146_detail::Block block;
    std::map<std::string,std::vector<round143_detail::Row>> expected;
};
inline Round146Controls& round146(){static Round146Controls c;return c;}
inline void round146ResetRun(){const bool enabled=round146().enabled;round146()=Round146Controls{};round146().enabled=enabled;}
namespace round146_detail {
inline CanonicalCompactModelArtifact embed(const Instance& instance,const CanonicalCompactModelArtifact& base,
                                         const std::filesystem::path& path){
    auto& c=round146();if(!c.enabled)return base;
    require(base.written&&fileSha256(base.path)==base.sha256,"base_identity");
    const auto support=round141_detail::supports(round141_detail::material(base.path),instance.V);
    long long b=0,q=0;std::vector<double> ratios(instance.V+1);
    for(int i=1;i<=instance.V;++i){b+=instance.initial[i];ratios[i]=1./instance.target[i];}
    for(int capacity:instance.Q)q+=capacity;const long long bm=std::max(0LL,b-q);
    const std::string input_sha=fileSha256(instance.path);
    if(!c.generated){
        c.input_sha=input_sha;c.bm=bm;c.b=b;c.ratios=ratios;c.support=support;
        c.block=block(support,ratios,bm,b);c.generated=true;
        std::ofstream f(path.parent_path()/"round146_root.json");f<<std::setprecision(17)
            <<"{\"applicable\":"<<(c.block.applicable?"true":"false")<<",\"input_SHA\":"<<std::quoted(input_sha)
            <<",\"Bminus\":"<<bm<<",\"B\":"<<b<<",\"S_lower\":"<<c.block.lower<<",\"S_upper\":"<<c.block.upper
            <<",\"generation_seconds\":"<<c.block.seconds<<",\"rows\":"<<c.block.rows.size()<<",\"states\":"<<c.block.states.size()
            <<",\"source_solves\":0,\"new_columns\":0,\"coefficient_policy\":\"exact_dyadic_bounds_outward_ratios_downward_coefficients\"}\n";
        f.close();require(bool(f),"root_evidence_write");
    }
    require(c.input_sha==input_sha&&c.ratios==ratios&&c.bm==bm&&c.b==b,"input_or_inventory_scope_changed");
    require(support.size()==c.support.size(),"scope_station_count");
    for(int i=1;i<=instance.V;++i)require(std::includes(c.support[i].begin(),c.support[i].end(),support[i].begin(),support[i].end()),"scope_support_expanded");
    auto rows=c.block.rows;
    for(auto& row:rows)for(auto it=row.coefficients.begin();it!=row.coefficients.end();){
        if(it->first=="G"){++it;continue;}const auto parts=round141_detail::split(it->first,'_');
        require(parts.size()==3,"selector_name");const int i=std::stoi(parts[1]),y=std::stoi(parts[2]);
        if(!std::binary_search(support.at(i).begin(),support.at(i).end(),y))it=row.coefficients.erase(it);else ++it;
    }
    auto out=base;
    if(!rows.empty()){
        out=round144_detail::append(base,rows,{},path,"GD");
        out.model_scope=base.model_scope+"_round146_GD";out.row_signature=base.row_signature+"|round146:"+out.sha256;
    }
    c.expected.emplace(out.sha256,std::move(rows));return out;
}
}
}
