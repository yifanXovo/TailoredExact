#pragma once
#include "Round144Research.hpp"

namespace ebrp {
struct Round145Controls { bool enabled=false; };
inline Round145Controls& round145(){static Round145Controls c;return c;}
namespace round145_detail {
// Same production-capped RN block; six explicitly listed additional rows, no
// additional columns. These finite caps remain integer-valid in the joint source.
inline round143_detail::Block augment(round143_detail::Block r,
    const std::vector<std::vector<int>>& support,const std::vector<double>& ratios,
    long long bm,long long b){
    if(!r.applicable)return r;
    using namespace round143_detail;
    const auto count=round140CountRows(support,ratios,bm,b);
    require(!count.infeasible,"joint_count_domain");const int n=int(support.size())-1;
    long long minimum=0,maximum=0;for(int i=1;i<=n;++i){minimum+=support[i].front();maximum+=support[i].back();}
    bm=std::max(bm,minimum);b=std::min(b,maximum);
    const auto addrow=[&](std::string name,std::map<std::string,double> terms,char sense,double rhs){
        for(auto it=terms.begin();it!=terms.end();)if(it->second==0)it=terms.erase(it);else ++it;
        double smallest=1;for(const auto& term:terms)smallest=std::min(smallest,std::fabs(term.second));
        int scale=0;while(std::ldexp(smallest,scale)<1e-12)require(++scale<1023,"joint_row_scale");
        for(auto& term:terms){term.second=std::ldexp(term.second,scale);require(std::isfinite(term.second),"joint_coefficient");}
        rhs=std::ldexp(rhs,scale);require(std::isfinite(rhs),"joint_rhs");
        r.rows.push_back({std::move(name),std::move(terms),sense,rhs});
    };
    for(int mode=1;mode<=2;++mode){
        std::map<std::string,double> terms;
        for(int i=1;i<=n;++i)for(int j=i+1;j<=n;++j)terms[h(i,j)]=1;
        const auto& coefficients=mode==1?count.tc:count.tc2;
        for(const auto& term:coefficients)terms[w(term.first.first,term.first.second)]=-term.second;
        // Signed coefficient and constant are rounded down by R140; w,t >= 0.
        if(mode==2)terms["rn_t"]=-count.constant;
        addrow("r145_NC"+std::to_string(mode),terms,'>',0);
    }
    for(int k=1;k<=4;++k){
        const double slope=(k==1||k==4)?r.lt:r.ut;
        const long long endpoint=(k==1||k==3)?bm:b;
        const char sense=k<=2?'>':'<';std::map<std::string,double> terms;
        for(int i=1;i<=n;++i){terms[Y(i)]=1;terms["Y_"+std::to_string(i)]=-slope;}
        terms["rn_t"]=-static_cast<double>(endpoint);
        // Only this RHS multiplication is inexact; outward rounding is paid.
        const double rhs=std::nextafter(-slope*static_cast<double>(endpoint),
            sense=='>'?-std::numeric_limits<double>::infinity():std::numeric_limits<double>::infinity());
        addrow("r145_TS"+std::to_string(k),terms,sense,rhs);
    }
    return r;
}
inline round143_detail::Block block(const Instance& instance,const CanonicalCompactModelArtifact& base){
    auto r=round144_detail::block(instance,base);std::vector<double> ratios(instance.V+1);
    long long b=0,q=0;for(int i=1;i<=instance.V;++i){b+=instance.initial[i];ratios[i]=1./instance.target[i];}
    for(int v:instance.Q)q+=v;
    return augment(std::move(r),round144().support,ratios,std::max(0LL,b-q),b);
}
}
}
