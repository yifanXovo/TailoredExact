#include "ServiceResourceCuts.hpp"
#include <algorithm>
#include <cfenv>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <limits>
#include <numeric>
#include <sstream>
#include <stdexcept>
namespace ebrp { namespace {
constexpr long long absent=std::numeric_limits<long long>::min()/4;
constexpr long long exact_limit=1LL<<52;
constexpr int dimension_limit=2048;
double down(double x){return std::nextafter(x,-std::numeric_limits<double>::infinity());}
double addLower(double a,double b){if(a==0)return b;if(b==0)return a;return std::max(0.0,down(a+b));}
double productLower(double a,int b){if(a==0||b==0)return 0;return std::max(0.0,down(a*b));}
bool arithmeticReady(){volatile double x=std::numeric_limits<double>::denorm_min();volatile double y=x+x;
    return std::numeric_limits<double>::is_iec559&&std::fegetround()==FE_TONEAREST&&y==2*std::numeric_limits<double>::denorm_min();}
std::string weightKey(int k,const std::vector<ServiceWeight>& w){std::ostringstream s;s<<k<<':';for(auto a:w)s<<a[0]<<','<<a[1]<<','<<a[2]<<';';return s.str();}
}
ServiceContract prepareServiceContract(const Instance& in,const NativeOtB1LinearModel& m){
    ServiceContract out;out.resource=prepareFleetContract(in,m);
    if(!out.resource.valid){out.reason=out.resource.reason;return out;}
    std::map<std::string,int> cols;for(std::size_t j=0;j<m.names.size();++j)cols.emplace(m.names[j],static_cast<int>(j));
    out.columns.resize(in.M,std::vector<std::array<int,3>>(in.V+1,{-1,-1,-1}));
    for(int k=0;k<in.M;++k)for(int i=1;i<=in.V;++i)for(int t=0;t<3;++t){
        const auto name=std::string(t==0?"p_":t==1?"d_":"z_")+std::to_string(k)+"_"+std::to_string(i);
        auto it=cols.find(name);if(it==cols.end()){out.reason="service_column_mapping";return out;}
        out.columns[k][i][t]=it->second;
    }
    out.valid=true;out.reason="audited_original_integer_service_model";out.identity=serviceContractJson(out);return out;
}
ServiceSupport proveServiceSupport(const FleetContract& c,int k,const std::vector<ServiceWeight>& w){
    ServiceSupport r;r.vehicle=k;r.weights=w;
    const auto n=c.initial.size();
    if(!c.valid||!arithmeticReady()||k<0||static_cast<std::size_t>(k)>=c.capacities.size()||
        n<2||n!=c.station_capacity.size()||w.size()!=n||c.shortest_lower.size()!=n||
        !std::isfinite(c.handling_lower)||c.handling_lower<0||!std::isfinite(c.horizon_upper)||c.horizon_upper<0){r.reason="invalid_support_contract";return r;}
    const int Q=c.capacities[k];if(Q<0){r.reason="invalid_capacity";return r;}
    std::vector<int>A(n),B(n);std::vector<double> ell(n);long long total=0,bound=0;
    for(std::size_t i=0;i<n;++i)if(c.shortest_lower[i].size()!=n){r.reason="shortest_shape";return r;}
    for(std::size_t i=1;i<n;++i){
        if(c.initial[i]<0||c.station_capacity[i]<c.initial[i]){r.reason="inventory_bounds";return r;}
        A[i]=std::min(c.initial[i],Q);B[i]=std::min(c.station_capacity[i]-c.initial[i],Q);total+=A[i];
        const double f=c.shortest_lower[0][i],b=c.shortest_lower[i][0];
        if(!std::isfinite(f)||f<0||!std::isfinite(b)||b<0){r.reason="travel_bounds";return r;}
        ell[i]=addLower(f,b);
        // Check BEFORE absolute value/multiplication, including LLONG_MIN.
        for(auto x:w[i])if(x<=-exact_limit||x>=exact_limit){r.reason="weight_range";return r;}
        const long long multipliers[3]={A[i],B[i],1};
        for(int t=0;t<3;++t){const auto a=std::llabs(w[i][t]);
            if(a && multipliers[t]>(exact_limit-1-bound)/a){r.reason="score_range";return r;}
            bound+=a*multipliers[t];}
    }
    // No quotient/floor exclusion: enumerate a finite integer domain using
    // downward resource sums. Uncertain arithmetic retains possibilities.
    int U=0;
    while(static_cast<long long>(U)<total&&U<=dimension_limit){
        const double lb=productLower(c.handling_lower,U+1);
        if(std::isfinite(lb)&&lb>c.horizon_upper)break;
        ++U;
    }
    if(U>dimension_limit){r.reason="unsupported_resource_dimension_no_bound";return r;}
    r.resource_limit=U;const int stride=U+1;
    std::vector<int> order(n-1);std::iota(order.begin(),order.end(),1);
    std::sort(order.begin(),order.end(),[&](int a,int b){return ell[a]!=ell[b]?ell[a]<ell[b]:a<b;});
    std::vector<long long> dp(static_cast<std::size_t>(stride)*stride,absent);dp[0]=0;
    for(std::size_t pos=0;pos<order.size();++pos){const int i=order[pos];auto next=dp;
        for(int p=0;p<=U;++p)for(int d=0;d<=U;++d){const auto v=dp[p*stride+d];if(v==absent)continue;
            for(int a=1;a<=std::min(A[i],U-p);++a){auto& cell=next[(p+a)*stride+d];cell=std::max(cell,v+w[i][0]*a+w[i][2]);}
            for(int b=1;b<=std::min(B[i],U-d);++b){auto& cell=next[p*stride+d+b];cell=std::max(cell,v+w[i][1]*b+w[i][2]);}
        }
        dp.swap(next);
        if(pos+1<order.size()&&ell[order[pos+1]]==ell[i])continue;
        int cap=-1;long long best=absent;
        for(int p=0;p<=U;++p){const double lb=addLower(ell[i],productLower(c.handling_lower,p));
            if(std::isfinite(lb)&&lb>c.horizon_upper)break;
            cap=p;for(int d=0;d<=p;++d)best=std::max(best,dp[p*stride+d]);}
        r.upper=std::max(r.upper,best);r.stations.push_back(i);r.pickup_caps.push_back(cap);r.level_maxima.push_back(best);
    }
    r.valid=true;r.reason="complete_integer_necessary_system_upper";return r;
}
std::vector<ServiceCut> separateServiceResources(const ServiceContract& c,const std::vector<double>& point,double margin,ServiceStatistics& stats){
    std::vector<ServiceCut> rows;
    if(!c.valid||point.size()!=static_cast<std::size_t>(c.resource.columns)||!std::isfinite(margin)||margin<0)throw std::runtime_error("service_separator_contract");
    for(auto v:point)if(!std::isfinite(v))throw std::runtime_error("service_nonfinite_point");
    if(stats.contract!=c.identity){stats.cache.clear();stats.order.clear();stats.contract=c.identity;}
    const auto& R=c.resource;const int V=static_cast<int>(R.initial.size())-1;
    auto retain=[&](ServiceCut r){
        double activity=0;for(std::size_t j=0;j<r.indices.size();++j)
            activity=down(activity+down(r.coefficients[j]*point[r.indices[j]]));
        r.activity_lower=activity;r.violation_lower=down(activity-r.rhs);
        if(!std::isfinite(r.rhs)||!std::isfinite(activity))throw std::runtime_error("service_row_arithmetic");
        if(r.violation_lower>margin){++stats.reliable;rows.push_back(std::move(r));}
    };
    // Two fixed structural direction rules. Weights are exact integers; actual
    // submitted coefficients/RHS divided by1024 are exact binary dyadics.
    for(int family=0;family<2;++family){ServiceCut combined;combined.key=std::to_string(family)+":";
        for(std::size_t k=0;k<R.capacities.size();++k){std::vector<ServiceWeight>w(V+1,{0,0,0});
            for(int i=1;i<=V;++i){auto cols=c.columns[k][i];const double p=point[cols[0]],d=point[cols[1]],z=point[cols[2]];
                if(p+d<=margin)continue;
                const int A=std::min(R.initial[i],R.capacities[k]),B=std::min(R.station_capacity[i]-R.initial[i],R.capacities[k]);
                long long alpha=std::llround(1024.0/std::max(1,A)),beta=std::llround(1024.0/std::max(1,B));
                if(family==0){if(p/std::max(1,A)>=d/std::max(1,B))beta=0;else alpha=0;}
                else{const bool pick=p>=d;const int bound=pick?A:B;
                    // Clamp BEFORE integer conversion. Selection has no role in
                    // validity, so questionable ratios merely choose a endpoint.
                    const double quantity=std::max(1.0,std::min(static_cast<double>(std::max(1,bound)),std::ceil((pick?p:d)/std::max(z,1e-6))));
                    const int q=static_cast<int>(quantity);if(pick)beta=0;else alpha=0;
                    w[i][2]=-(q-1)*(alpha+beta);}
                w[i][0]=alpha;w[i][1]=beta;
            }
            ++stats.directions;const auto key=weightKey(static_cast<int>(k),w);ServiceSupport proof;
            auto found=stats.cache.find(key);
            if(found!=stats.cache.end()){proof=found->second;++stats.cache_hits;}
            else{proof=proveServiceSupport(R,static_cast<int>(k),w);++stats.dp_calls;
                if(!proof.valid)throw std::runtime_error("service_support_failed:"+proof.reason);
                if(stats.cache.size()>=256){stats.cache.erase(stats.order.front());stats.order.pop_front();}
                stats.order.push_back(key);stats.cache.emplace(key,proof);}
            // A fleet sum can hide one violated car behind another car's slack.
            // The same computed support is valid for the single-car subset.
            ServiceCut single;single.key="single:"+std::to_string(family)+":"+key;
            single.rhs=static_cast<double>(proof.upper)/1024;single.proofs.push_back(proof);
            combined.key+=key;combined.rhs=std::nextafter(combined.rhs+static_cast<double>(proof.upper)/1024,std::numeric_limits<double>::infinity());
            combined.proofs.push_back(std::move(proof));
            for(int i=1;i<=V;++i)for(int t=0;t<3;++t)if(w[i][t]){
                const int j=c.columns[k][i][t];const double a=static_cast<double>(w[i][t])/1024;
                combined.indices.push_back(j);combined.coefficients.push_back(a);single.indices.push_back(j);single.coefficients.push_back(a);}
            retain(std::move(single));
        }
        retain(std::move(combined));
    }
    std::sort(rows.begin(),rows.end(),[](const auto&a,const auto&b){return a.violation_lower!=b.violation_lower?a.violation_lower>b.violation_lower:a.key<b.key;});
    if(rows.size()>2)rows.resize(2);return rows;
}
std::string serviceSupportJson(const ServiceSupport&r){std::ostringstream s;s<<std::setprecision(17)<<"{\"valid\":"<<(r.valid?"true":"false")<<",\"vehicle\":"<<r.vehicle<<",\"upper\":"<<r.upper<<",\"resource_limit\":"<<r.resource_limit<<",\"weights\":[";
    for(std::size_t i=0;i<r.weights.size();++i){if(i)s<<',';auto w=r.weights[i];s<<'['<<w[0]<<','<<w[1]<<','<<w[2]<<']';}s<<"],\"levels\":[";
    for(std::size_t i=0;i<r.stations.size();++i){if(i)s<<',';s<<'['<<r.stations[i]<<','<<r.pickup_caps[i]<<','<<r.level_maxima[i]<<']';}s<<"]}";return s.str();}
std::string serviceContractJson(const ServiceContract&c){std::ostringstream s;s<<"{\"resource\":"<<fleetContractJson(c.resource)<<",\"service_columns\":[";
    for(std::size_t k=0;k<c.columns.size();++k){if(k)s<<',';s<<'[';for(std::size_t i=0;i<c.columns[k].size();++i){if(i)s<<',';auto a=c.columns[k][i];s<<'['<<a[0]<<','<<a[1]<<','<<a[2]<<']';}s<<']';}s<<"]}";return s.str();}
} // namespace ebrp
