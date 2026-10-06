#include "ObjectiveResourceCompression.hpp"
#include <algorithm>
#include <cfenv>
#include <cmath>
#include <limits>
#include <map>
#include <set>
#include <stdexcept>
namespace ebrp { namespace {
struct Interval { double lo=0,hi=0; };
double down(double v){return std::nextafter(v,-std::numeric_limits<double>::infinity());}
double up(double v){return std::nextafter(v,std::numeric_limits<double>::infinity());}
void finite(double v){if(!std::isfinite(v))throw std::runtime_error("resource_compression_nonfinite");}
Interval add(Interval a,Interval b){
    if(a.lo==0&&a.hi==0)return b;
    if(b.lo==0&&b.hi==0)return a;
    Interval r{down(a.lo+b.lo),up(a.hi+b.hi)};finite(r.lo);finite(r.hi);return r;
}
Interval product(double a,double b){
    finite(a);finite(b);if(a==0||b==0)return {};
    const double v=a*b;finite(v);Interval r{down(v),up(v)};finite(r.lo);finite(r.hi);return r;
}
void validate(const ObjectiveResourceRow& r,std::size_t columns){
    if(r.scope.empty()||r.vehicle<0||r.indices.size()!=r.coefficients.size())
        throw std::runtime_error("resource_compression_mapping");
    finite(r.rhs);finite(r.multiplier);
    if(r.multiplier<0)throw std::runtime_error("resource_compression_negative_multiplier");
    std::set<int> seen;
    for(std::size_t j=0;j<r.indices.size();++j){
        const int i=r.indices[j];finite(r.coefficients[j]);
        if(i<0||static_cast<std::size_t>(i)>=columns||!seen.insert(i).second)
            throw std::runtime_error("resource_compression_column");
    }
}
}
double resourceMultiplier(double pi,char sense,int objective_sense){
    finite(pi);
    if(sense!='<'||objective_sense!=1||pi>0)
        throw std::runtime_error("resource_compression_dual_convention");
    return -pi;
}
std::vector<int> activeResourceRows(const std::vector<ObjectiveResourceRow>& rows){
    std::vector<int> result;
    for(std::size_t j=0;j<rows.size();++j){finite(rows[j].multiplier);
        if(rows[j].multiplier<0)throw std::runtime_error("resource_compression_negative_multiplier");
        if(rows[j].multiplier>0)result.push_back(static_cast<int>(j));}
    return result;
}
std::vector<CompressedResourceRow> compressObjectiveResources(
    const std::vector<ObjectiveResourceRow>& rows,const std::vector<double>& lower,
    const std::vector<double>& upper,bool fleet){
    volatile double subnormal=std::numeric_limits<double>::denorm_min();
    volatile double twice_subnormal=subnormal+subnormal;
    if(lower.size()!=upper.size()||std::fegetround()!=FE_TONEAREST||!std::numeric_limits<double>::is_iec559||
       twice_subnormal!=2*std::numeric_limits<double>::denorm_min())
        throw std::runtime_error("resource_compression_arithmetic_or_bounds");
    for(std::size_t i=0;i<lower.size();++i)
        if(std::isnan(lower[i])||std::isnan(upper[i])||lower[i]>upper[i])
            throw std::runtime_error("resource_compression_bounds");
    std::map<int,std::vector<int>> groups;std::string scope;
    for(std::size_t j=0;j<rows.size();++j){const auto& r=rows[j];validate(r,lower.size());
        if(scope.empty())scope=r.scope;
        if(r.scope!=scope)throw std::runtime_error("resource_compression_scope");
        if(r.multiplier>0)groups[fleet?0:r.vehicle].push_back(static_cast<int>(j));}
    std::vector<CompressedResourceRow> result;
    for(const auto& group:groups){
        std::map<int,Interval> a;Interval b;
        for(int j:group.second){const auto& r=rows[j];b=add(b,product(r.multiplier,r.rhs));
            for(std::size_t t=0;t<r.indices.size();++t)
                a[r.indices[t]]=add(a[r.indices[t]],product(r.multiplier,r.coefficients[t]));}
        CompressedResourceRow out;out.scope=scope;out.vehicle=fleet?-1:group.first;out.source_rows=group.second;
        Interval correction;
        for(const auto& term:a){const int i=term.first;const auto range=term.second;
            // A representable interior coefficient, without deleting tiny terms.
            const double coefficient=range.lo/2+range.hi/2;finite(coefficient);
            const double dl=down(coefficient-range.hi),du=up(coefficient-range.lo);
            if(range.lo!=range.hi){finite(lower[i]);finite(upper[i]);}
            double margin=0;
            if(dl!=0||du!=0){finite(lower[i]);finite(upper[i]);
                if(std::fabs(lower[i])>=1e100||std::fabs(upper[i])>=1e100)
                    throw std::runtime_error("resource_compression_unbounded_conversion");
                margin=std::max({product(dl,lower[i]).hi,product(dl,upper[i]).hi,
                    product(du,lower[i]).hi,product(du,upper[i]).hi});}
            correction=add(correction,{margin,margin});
            if(coefficient!=0){out.indices.push_back(i);out.coefficients.push_back(coefficient);}
        }
        out.compensation_upper=correction.hi;out.rhs=add(b,correction).hi;finite(out.rhs);
        result.push_back(std::move(out));
    }
    return result;
}
}
