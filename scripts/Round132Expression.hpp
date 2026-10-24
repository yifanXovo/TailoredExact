#pragma once
// Research-only helper; included only by separately generated translation units.
// Frozen src/include and original E3 are never modified.
#include "IntervalRowFactory.hpp"
#include <cmath>
#include <stdexcept>
#include <string>
#include <vector>

namespace ebrp {
inline std::string& round132Expression() { static std::string value="off"; return value; }
inline void round132SetExpression(const std::string& value) {
    if(value!="off" && value!="geom" && value!="sp")
        throw std::runtime_error("Round132 expression must be off, geom or sp");
    round132Expression()=value;
}
inline bool round132SP() { return round132Expression()=="sp"; }
inline std::vector<CanonicalLinearRow> round132Rows(
    const std::vector<CanonicalLinearRow>& input, double w_lower, double w_upper) {
    if(round132Expression()=="off") return input;
    std::vector<CanonicalLinearRow> kept,lower,upper;
    for(auto row:input) {
        if(round132Expression()=="geom") {
            if(row.family=="gini_pairwise_spread" || row.family=="low_gini_centering_band" ||
               row.family=="variable_s_low_gini_centering") continue;
            kept.push_back(std::move(row)); continue;
        }
        auto w=row.coefficients.find("W_SP");
        if(w==row.coefficients.end() || w->second==0.) {kept.push_back(std::move(row));continue;}
        if(row.sense=='E')throw std::runtime_error("Unexpected W equality");
        if(row.sense=='G') {
            for(auto& c:row.coefficients)c.second=-c.second;
            row.rhs=-row.rhs;row.sense='L';
        }
        if(row.coefficients.at("W_SP")<0.)lower.push_back(std::move(row));
        else upper.push_back(std::move(row));
    }
    if(!round132SP())return kept;
    if(lower.size()!=2 || (upper.size()!=2 && upper.size()!=3))
        throw std::runtime_error("Unexpected actual W uses; exact projection not admitted");
    CanonicalLinearRow lo,hi;
    lo.coefficients["W_SP"]=-1.;lo.rhs=-w_lower;lo.sense='L';
    hi.coefficients["W_SP"]=1.;hi.rhs=w_upper;hi.sense='L';
    lower.push_back(lo);upper.push_back(hi);
    // Fourier-Motzkin on the *actual emitted double coefficients* and W box.
    // Every pair is retained, including P-domain implications and degeneracies.
    // Exact real arithmetic gives the complete projection. Binary64 output is
    // separately qualified against exact-rational coefficient arithmetic.
    for(const auto& l:lower)for(const auto& u:upper) {
        const long double a=-static_cast<long double>(l.coefficients.at("W_SP"));
        const long double b=static_cast<long double>(u.coefficients.at("W_SP"));
        std::map<std::string,long double> sum;
        for(const auto& c:l.coefficients)if(c.first!="W_SP")sum[c.first]+=b*c.second;
        for(const auto& c:u.coefficients)if(c.first!="W_SP")sum[c.first]+=a*c.second;
        CanonicalLinearRow r;r.family="round132_exact_W_projection";r.sense='L';
        r.rhs=static_cast<double>(b*l.rhs+a*u.rhs);
        r.proof_tag="all_lower_upper_pairs_including_actual_W_box";
        for(const auto& c:sum)if(c.second!=0.)r.coefficients[c.first]=static_cast<double>(c.second);
        kept.push_back(std::move(r));
    }
    return kept;
}
}
