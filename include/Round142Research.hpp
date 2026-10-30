#pragma once
#include "Round140Research.hpp"
#include <map>
#include <string>
#include <vector>
#include <limits>
#include <cmath>
#include <stdexcept>

namespace ebrp {
// Independent, default-off control. No public SolveOptions or model ABI change.
struct Round142Controls {
    std::string products="off";
    bool enabled()const{return products!="off";}
    void set(const std::string& value) {
        if(value!="off"&&value!="selected"&&value!="all")
            throw std::runtime_error("Round142 count products must be off/selected/all");
        products=value;
    }
};
inline Round142Controls& round142(){static Round142Controls c;return c;}

// Called only inside a count-restricted R141 proof source. W is expanded in
// existing state_g columns. Row, Choice and Grid reuse the R141 exact domain.
template<class Row,class Choice,class Grid>
inline std::vector<Row> round142SourceRows(const Choice& c,const Grid& grid,
    int side,double alpha,double beta) {
    if(!round142().enabled())return {};
    if((side!=0&&side!=1)||!std::isfinite(alpha)||!std::isfinite(beta)||
        alpha<0||alpha>beta||alpha!=c.a||beta!=c.z||grid.exponent!=c.exponent)
        throw std::runtime_error("Round142 inconsistent actual source domain");
    using namespace round140_detail;
    std::vector<Row> rows;
    std::size_t index=0;
    for(auto r:grid.rows) {
        if(side==0&&r.t>=c.threshold)r.u=std::min(r.u,c.pivot);
        if(side==1&&r.t<=c.threshold)r.ell=std::max(r.ell,c.pivot+1);
        if(r.ell>r.u)throw std::runtime_error("Round142 incompatible propagated count interval");
        if(round142().products=="selected"&&r.t!=c.threshold)continue;
        std::vector<std::string> keys;
        for(std::size_t i=1;i<c.support.size();++i)for(int y:c.support[i])
            if(mul(units(c.ratios[i],c.exponent),y)>=r.t)
                keys.push_back("state_"+std::to_string(i)+"_"+std::to_string(y));
        // Keep linear ranges explicitly, including alpha==beta. The source
        // already has one selected-side inequality, so append only its mate.
        for(int upper=0;upper<2;++upper) {
            if(r.t==c.threshold&&((upper&&side==0)||(!upper&&side==1)))continue;
            Row range;range.name="r142_range_"+std::to_string(index)+"_"+std::to_string(upper);
            double sign=upper?-1.:1.;range.rhs=sign*(upper?r.u:r.ell);
            for(const auto& key:keys)range.coefficients[key]=sign;
            rows.push_back(std::move(range));
        }
        const double slopes[4]={alpha,beta,beta,alpha};
        const int bounds[4]={r.ell,r.u,r.ell,r.u};
        for(int facet=0;facet<4;++facet) {
            Row row;row.name="r142_cp_"+std::to_string(index)+"_"+std::to_string(facet);
            double sign=facet<2?1.:-1.,slope=slopes[facet],bound=bounds[facet];
            for(const auto& key:keys) {
                if(slope!=0)row.coefficients[key]=-sign*slope;
                row.coefficients["state_g_"+key.substr(6)]=sign;
            }
            if(bound!=0)row.coefficients["G"]=-sign*bound;
            row.rhs=-sign*slope*bound;
            if(!std::isfinite(row.rhs))throw std::runtime_error("Round142 nonfinite product RHS");
            // All rows are >=. One outward ULP encloses the exact dyadic
            // endpoint * integer product, as in the mature R138 writer.
            if(slope!=0&&bound!=0)
                row.rhs=std::nextafter(row.rhs,-std::numeric_limits<double>::infinity());
            double smallest=1;
            for(const auto& term:row.coefficients)smallest=std::min(smallest,std::fabs(term.second));
            int exponent=0;
            while(std::ldexp(smallest,exponent)<1e-12) {
                if(++exponent>1023)throw std::runtime_error("Round142 product scale overflow");
            }
            for(auto& term:row.coefficients) {
                term.second=std::ldexp(term.second,exponent);
                if(!std::isfinite(term.second))throw std::runtime_error("Round142 scaled coefficient overflow");
            }
            row.rhs=std::ldexp(row.rhs,exponent);
            if(!std::isfinite(row.rhs))throw std::runtime_error("Round142 scaled RHS overflow");
            rows.push_back(std::move(row));
        }
        ++index;
    }
    if(index==0)throw std::runtime_error("Round142 selected threshold absent from actual support");
    return rows;
}
}
