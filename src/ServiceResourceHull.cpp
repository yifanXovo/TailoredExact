#include "ServiceResourceHull.hpp"
#include <algorithm>
#include <cmath>
#include <iomanip>
#include <limits>
#include <numeric>
#include <set>
#include <sstream>
#include <stdexcept>
namespace ebrp {namespace {
double up(double a){return std::nextafter(a,std::numeric_limits<double>::infinity());}
double down(double a){return std::nextafter(a,-std::numeric_limits<double>::infinity());}
double addLo(double a,double b){return a==0?b:b==0?a:std::max(0.,down(a+b));}
double mulLo(double a,int b){return a==0||b==0?0.:std::max(0.,down(a*b));}
std::vector<std::array<int,3>> widths(const FleetContract&c,int k){
    std::vector<std::array<int,3>>w(c.initial.size(),{0,0,0});
    for(std::size_t i=1;i<w.size();++i){const int A=std::min(c.initial[i],c.capacities[k]),B=std::min(c.station_capacity[i]-c.initial[i],c.capacities[k]);w[i]={A,B,A>0||B>0?1:0};}return w;
}
double combinationResidual(const ServicePoint&point,const std::vector<std::array<int,3>>&s,const HullMembership&r){
    double masslo=0,masshi=0;for(double a:r.lambda_raw){masslo=std::max(0.,down(masslo+a));masshi=up(masshi+a);}
    if(masslo<=0||!std::isfinite(masshi))return std::numeric_limits<double>::infinity();
    double residual=0;
    for(std::size_t i=1;i<point.size();++i)for(int t=0;t<3;++t){
        double lo=0,hi=0;
        for(std::size_t j=0;j<r.plans.size();++j){const double a=r.lambda_raw[j];if(!a||!r.plans[j][i][t])continue;
            lo=std::max(0.,down(lo+std::max(0.,down(a*r.plans[j][i][t]))));hi=up(hi+up(a*r.plans[j][i][t]));}
        lo=std::max(0.,down(lo/masshi));hi=up(hi/masslo);
        const double error=std::max(up(point[i][t]-lo),up(hi-point[i][t]));
        residual=std::max(residual,s[i][t]?up(error/s[i][t]):error);
    }return residual;
}
}
HullMembership classifyServiceHull(const ServiceContract&c,int k,const ServicePoint&point,const HullLpSolver&solve,const std::vector<int>&anchors,double tolerance,const HullTrace&trace){
    HullMembership result;
    if(!c.valid||k<0||static_cast<std::size_t>(k)>=c.columns.size()||point.size()!=c.resource.initial.size()||!std::isfinite(tolerance)||tolerance<=0)throw std::runtime_error("hull_contract");
    for(auto r:point)for(auto a:r)if(!std::isfinite(a))throw std::runtime_error("hull_nonfinite_point");
    const auto s=widths(c.resource,k);const std::size_t n=point.size();
    for(std::size_t i=1;i<n;++i)for(int t=0;t<3;++t)if(!s[i][t]&&std::fabs(point[i][t])>tolerance){result.reason="zero_width_residual";return result;}
    std::vector<ServicePlan>library(1,ServicePlan(n,{0,0,0}));std::set<ServicePlan>seen;seen.insert(library[0]);
    long long total_width=0;for(auto row:s)for(int value:row){
        if(value<0||value>std::numeric_limits<long long>::max()-total_width){result.reason="physical_width_range";return result;}total_width+=value;}
    const double ratio=4.*std::max(1LL,total_width)/tolerance;
    if(!std::isfinite(ratio)||ratio>std::ldexp(1.,48)){result.reason="quantization_precision_contract";return result;}
    const int bits=std::max(30,static_cast<int>(std::ceil(std::log2(ratio))));
    const double scale=std::ldexp(1.,bits); // exact dyadic; error envelope <=tol/8
    while(library.size()<=4096){
        ++result.lp_calls;auto master=solve(library);
        if(!master.optimal){result.reason="master_incomplete";return result;}
        if(master.lambda.size()!=library.size()||master.direction.size()!=n)throw std::runtime_error("hull_master_shape");
        result.plans.clear();result.lambda_raw.clear();
        for(std::size_t j=0;j<library.size();++j){const double a=master.lambda[j];if(!std::isfinite(a))throw std::runtime_error("hull_lambda_nonfinite");
            if(a>0){std::string why;if(!validateServicePlan(c.resource,k,library[j],why,anchors))throw std::runtime_error("hull_illegal_column:"+why);
                result.plans.push_back(library[j]);result.lambda_raw.push_back(a);}}
        result.distance_upper=combinationResidual(point,s,result);
        if(result.distance_upper<=tolerance){result.status="INSIDE";result.reason="explicit_rational_combination_interval_verified";return result;}
        double norm=0;for(std::size_t i=1;i<n;++i)for(int t=0;t<3;++t){const double a=master.direction[i][t];if(!std::isfinite(a))throw std::runtime_error("hull_direction_nonfinite");norm=up(norm+up(std::fabs(a)*s[i][t]));}
        if(norm<=0||!std::isfinite(norm)){result.reason="invalid_dual_norm";return result;}
        std::vector<ServiceWeight>w(n,{0,0,0});
        for(std::size_t i=1;i<n;++i)for(int t=0;t<3;++t)if(s[i][t])w[i][t]=std::llround((master.direction[i][t]/std::max(1.,norm))*scale);
        ++result.dp_calls;
        if(trace)trace("{\"event\":\"DP_begin\",\"vehicle\":"+std::to_string(k)+",\"call\":"+std::to_string(result.dp_calls)+"}");
        auto proof=proveServiceSupport(c.resource,k,w,true,anchors);
        if(trace)trace("{\"event\":\"DP_return\",\"proof\":"+serviceSupportJson(proof)+"}");
        if(!proof.valid){
            if(proof.reason!="unsupported_resource_dimension_no_bound"&&
               proof.reason!="witness_memory_limit_no_bound"&&proof.reason!="weight_range"&&proof.reason!="score_range")
                throw std::runtime_error("hull_support_validation:"+proof.reason);
            result.reason="support_unknown:"+proof.reason;return result;
        }
        ServiceCut cut;cut.proofs.push_back(proof);double activity=0,qnorm=0;
        cut.rhs=static_cast<double>(proof.upper)/scale;
        for(std::size_t i=1;i<n;++i)for(int t=0;t<3;++t)if(w[i][t]){const double a=static_cast<double>(w[i][t])/scale;
            cut.indices.push_back(c.columns[k][i][t]);cut.coefficients.push_back(a);activity=down(activity+down(a*point[i][t]));qnorm=up(qnorm+up(std::fabs(a)*s[i][t]));}
        cut.activity_lower=activity;cut.violation_lower=down(activity-cut.rhs);
        if(qnorm>0&&cut.violation_lower>up(tolerance*qnorm)){result.status="OUTSIDE";result.reason="complete_domain_dyadic_support_row";result.cut=std::move(cut);return result;}
        if(!seen.insert(proof.solution).second){++result.duplicates;result.reason="duplicate_without_membership";return result;}
        library.push_back(std::move(proof.solution));
    }
    result.reason="structural_column_limit";return result;
}
std::vector<int> chooseServiceAnchors(const FleetContract&c,int k,const HullMembership&r){
    if(r.plans.empty()||r.plans.size()!=r.lambda_raw.size())return {};
    const int V=static_cast<int>(c.initial.size())-1;std::vector<int>pool;
    for(int i=1;i<=V;++i)if(std::any_of(r.plans.begin(),r.plans.end(),[&](const auto&p){return p[i][2]!=0;}))pool.push_back(i);
    std::vector<int>P(r.plans.size());std::vector<double>solo(r.plans.size());
    for(std::size_t j=0;j<r.plans.size();++j){std::string why;if(!validateServicePlan(c,k,r.plans[j],why))throw std::runtime_error("anchor_source_plan:"+why);
        for(int i=1;i<=V;++i){P[j]+=r.plans[j][i][0];if(r.plans[j][i][2])solo[j]=std::max(solo[j],addLo(c.shortest_lower[0][i],c.shortest_lower[i][0]));}}
    double best=0;std::vector<int>chosen;
    auto assess=[&](const std::vector<int>&A){const auto tau=serviceAnchorTravel(c,A);double score=0;
        for(std::size_t j=0;j<r.plans.size();++j){int mask=0;for(std::size_t q=0;q<A.size();++q)if(r.plans[j][A[q]][2])mask|=1<<q;
            const double lower=addLo(std::max(solo[j],tau[mask]),mulLo(c.handling_lower,P[j]));
            score+=r.lambda_raw[j]*std::max(0.,down(lower-c.horizon_upper));}
        if(score>best){best=score;chosen=A;}};
    // Uniform structural search, independent of instance names/history/timers.
    for(std::size_t a=0;a<pool.size();++a)for(std::size_t b=a+1;b<pool.size();++b)assess({pool[a],pool[b]});
    for(std::size_t a=0;a<pool.size();++a)for(std::size_t b=a+1;b<pool.size();++b)for(std::size_t d=b+1;d<pool.size();++d)assess({pool[a],pool[b],pool[d]});
    return chosen;
}
std::string hullMembershipJson(const HullMembership&r){std::ostringstream s;s<<std::setprecision(17)<<"{\"status\":"<<std::quoted(r.status)<<",\"reason\":"<<std::quoted(r.reason)<<",\"lp_calls\":"<<r.lp_calls<<",\"dp_calls\":"<<r.dp_calls<<",\"duplicates\":"<<r.duplicates<<",\"distance_upper\":";
    if(std::isfinite(r.distance_upper))s<<r.distance_upper;else s<<"null";
    s<<",\"combination\":[";for(std::size_t j=0;j<r.plans.size();++j){if(j)s<<',';s<<"{\"lambda_raw\":"<<r.lambda_raw[j]<<",\"plan\":[";
        for(std::size_t i=0;i<r.plans[j].size();++i){if(i)s<<',';auto a=r.plans[j][i];s<<'['<<a[0]<<','<<a[1]<<','<<a[2]<<']';}s<<"]}";}s<<"],\"row\":{\"rhs\":"<<r.cut.rhs<<",\"activity_lower\":"<<r.cut.activity_lower<<",\"violation_lower\":"<<r.cut.violation_lower<<",\"columns\":[";
    for(std::size_t j=0;j<r.cut.indices.size();++j){if(j)s<<',';s<<'['<<r.cut.indices[j]<<','<<r.cut.coefficients[j]<<']';}s<<"],\"proofs\":[";
    for(std::size_t j=0;j<r.cut.proofs.size();++j){if(j)s<<',';s<<serviceSupportJson(r.cut.proofs[j]);}s<<"]}}";return s.str();}
} // namespace ebrp
