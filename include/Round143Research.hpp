#pragma once
#include "Round140Research.hpp"
#include <iomanip>
#include <numeric>
#include <sstream>

namespace ebrp {
struct Round143Controls { bool rn=false; };
inline Round143Controls& round143() { static Round143Controls c;return c; }
namespace round143_detail {
inline void require(bool ok,const std::string& why) {
    if(!ok)throw std::runtime_error("round143_"+why);
}
struct Row {std::string name;std::map<std::string,double> coefficients;char sense='=';double rhs=0;};
struct Block {
    bool applicable=false,infeasible=false;
    double sl=0,su=0,lt=0,ut=0;
    std::map<std::string,std::pair<double,double>> columns;
    std::vector<Row> rows;
};
inline std::string state(int i,int y) {return "state_"+std::to_string(i)+"_"+std::to_string(y);}
inline std::string w(int i,int y) {return "rn_w_"+std::to_string(i)+"_"+std::to_string(y);}
inline std::string Y(int i) {return "rn_Y_"+std::to_string(i);}
inline std::string h(int i,int j) {return "rn_h_"+std::to_string(i)+"_"+std::to_string(j);}
inline std::string emit(const Row& r) {
    std::ostringstream out;out<<std::setprecision(17)<<' '<<r.name<<": ";bool first=true;
    for(const auto& [name,value]:r.coefficients)if(value) {
        out<<(first?(value<0?"- ":""):(value<0?" - ":" + "))<<std::fabs(value)<<' '<<name;first=false;
    }
    if(first)out<<"0 G";
    out<<(r.sense=='>'?" >= ":r.sense=='<'?" <= ":" = ")<<r.rhs<<'\n';return out.str();
}
inline Block block(const std::vector<std::vector<int>>& support,const std::vector<double>& c,
        long long bm,long long b) {
    using namespace round140_detail;Block r;int n=int(support.size())-1;
    require(n>0&&c.size()==support.size()&&0<=bm&&bm<=b&&b<=9007199254740992LL,"scope_shape");
    int exponent=0;long long minimum=0,maximum=0;std::vector<int> order(n);
    for(int i=1;i<=n;++i) {
        require(!support[i].empty()&&std::is_sorted(support[i].begin(),support[i].end())&&support[i].front()>=0,"support");
        require(std::isfinite(c[i])&&c[i]>0,"positive_actual_ratio");
        minimum+=support[i].front();maximum+=support[i].back();
        int e=0;std::frexp(c[i],&e);exponent=std::min(exponent,e-53);order[i-1]=i;
    }
    bm=std::max(bm,minimum);b=std::min(b,maximum);
    if(bm>b) {r.infeasible=true;r.rows.push_back({"rn_infeasible",{},'<',-1});return r;}
    std::sort(order.begin(),order.end(),[&](int i,int j){return c[i]<c[j]||(c[i]==c[j]&&i<j);});
    const auto extremum=[&](long long total,bool reverse) {
        Int value=0;long long remaining=total-minimum;
        for(int i=1;i<=n;++i)value=add(value,mul(units(c[i],exponent),support[i].front()));
        for(int k=0;k<n;++k) {
            int i=order[reverse?n-1-k:k];long long take=std::min(remaining,static_cast<long long>(support[i].back())-support[i].front());
            value=add(value,mul(units(c[i],exponent),take));remaining-=take;
        }
        require(remaining==0,"inventory_fill");return value;
    };
    const Int lower=extremum(bm,false),upper=extremum(b,true);
    if(lower<=0)return r; // Retain the original zero-denominator convention.
    require(upper>=lower,"denominator_order");
    // Exact dyadic sums first; directed conversion encloses accumulated error.
    // A subsequent outward reciprocal encloses its own single rounding.
    r.sl=down(lower,exponent);r.su=-down(-upper,exponent);
    require(r.sl>0&&std::isfinite(r.su),"denominator_conversion");
    r.lt=std::nextafter(1./r.su,-std::numeric_limits<double>::infinity());
    r.ut=std::nextafter(1./r.sl,std::numeric_limits<double>::infinity());
    require(r.lt>0&&std::isfinite(r.ut)&&r.lt<=r.ut,"reciprocal_conversion");r.applicable=true;
    r.columns["rn_t"]={r.lt,r.ut};
    const auto addrow=[&](std::string name,std::map<std::string,double> terms,char sense,double rhs=0) {
        for(auto it=terms.begin();it!=terms.end();)if(it->second==0)it=terms.erase(it);else ++it;
        // Preserve the actual coefficients; exact positive power-of-two scaling
        // prevents the Native LP reader from discarding a tiny new coefficient.
        double smallest=1;for(const auto& term:terms)smallest=std::min(smallest,std::fabs(term.second));
        int scale=0;while(std::ldexp(smallest,scale)<1e-12)require(++scale<1023,"row_scale");
        for(auto& term:terms){term.second=std::ldexp(term.second,scale);require(std::isfinite(term.second),"scaled_coefficient");}
        rhs=std::ldexp(rhs,scale);require(std::isfinite(rhs),"scaled_rhs");
        r.rows.push_back({std::move(name),std::move(terms),sense,rhs});
    };
    std::map<std::string,double> normalization,gini;gini["G"]=-n;
    for(int i=1;i<=n;++i) {
        // These finite caps are redundant in the projection: Yhat<=M_i*t,
        // and |v_i-v_j|<=1 when v>=0 and sum(v)=1.
        double cap=support[i].back()==0?0:std::nextafter(r.ut*support[i].back(),std::numeric_limits<double>::infinity());
        require(std::isfinite(cap),"inventory_column_cap");r.columns[Y(i)]={0,cap};normalization[Y(i)]=c[i];
        std::map<std::string,double> mass,inventory;mass["rn_t"]=-1;inventory[Y(i)]=1;
        for(int y:support[i]) {
            r.columns[w(i,y)]={0,r.ut};mass[w(i,y)]=1;inventory[w(i,y)]=-y;
            addrow("rn_lb_"+std::to_string(i)+"_"+std::to_string(y),{{w(i,y),1},{state(i,y),-r.lt}},'>');
            addrow("rn_ub_"+std::to_string(i)+"_"+std::to_string(y),{{w(i,y),1},{state(i,y),-r.ut}},'<');
        }
        addrow("rn_mass_"+std::to_string(i),mass,'=');addrow("rn_inventory_"+std::to_string(i),inventory,'=');
    }
    addrow("rn_normalization",normalization,'=',1);
    for(int i=1;i<=n;++i)for(int j=i+1;j<=n;++j) {
        r.columns[h(i,j)]={0,1};gini[h(i,j)]=1;
        addrow("rn_abs_p_"+std::to_string(i)+"_"+std::to_string(j),{{h(i,j),1},{Y(i),-c[i]},{Y(j),c[j]}},'>');
        addrow("rn_abs_m_"+std::to_string(i)+"_"+std::to_string(j),{{h(i,j),1},{Y(i),c[i]},{Y(j),-c[j]}},'>');
    }
    addrow("rn_gini",gini,'<');return r;
}
}
}
