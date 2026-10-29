#pragma once

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

namespace ebrp {
// Independent research switch; old stock/placement flags keep their meanings.
struct Round140Controls {
    std::string counts = "off";
    bool enabled() const { return counts != "off"; }
    void set(const std::string& value) {
        if (value != "off" && value != "tc" && value != "tc2")
            throw std::runtime_error("Round140 counts must be off, tc or tc2");
        counts = value;
    }
};
inline Round140Controls& round140() { static Round140Controls c; return c; }

// Binary64 ratios are dyadic rationals. A common power-of-two unit makes all
// threshold comparisons and coefficient sums exact. Checked arithmetic fails
// closed outside this finite representation; no approximate threshold merging.
namespace round140_detail {
using Int = __int128;
inline Int add(Int a, Int b) {
    Int result;
    if (__builtin_add_overflow(a,b,&result)) throw std::runtime_error("TC2 exact sum overflow");
    return result;
}
inline Int mul(Int a, Int b) {
    Int result;
    if (__builtin_mul_overflow(a,b,&result)) throw std::runtime_error("TC2 exact product overflow");
    return result;
}
inline Int units(double value, int exponent) {
    if (value == 0) return 0;
    if (!std::isfinite(value)) throw std::runtime_error("TC2 nonfinite coefficient");
    int e=0;
    const double fraction=std::frexp(std::fabs(value),&e);
    std::uint64_t mantissa=static_cast<std::uint64_t>(std::ldexp(fraction,53));
    int shift=e-53-exponent;
    Int result=static_cast<Int>(mantissa);
    if (shift<0) {
        if (-shift>=64 || (mantissa & ((std::uint64_t(1)<<(-shift))-1)))
            throw std::runtime_error("TC2 coefficient is not in common dyadic units");
        result=static_cast<Int>(mantissa>>(-shift));
    } else {
        for (int k=0;k<shift;++k) result=mul(result,2);
    }
    return value<0 ? -result : result;
}
inline double down(Int value,int exponent) {
    if (!value) return 0;
    double loaded=std::ldexp(static_cast<double>(value),exponent);
    if (!std::isfinite(loaded) || loaded==0)
        throw std::runtime_error("TC2 coefficient conversion outside supported range");
    if (units(loaded,exponent)>value)
        loaded=std::nextafter(loaded,-std::numeric_limits<double>::infinity());
    if (units(loaded,exponent)>value) throw std::runtime_error("TC2 directed rounding failed");
    return loaded;
}
}

struct Round140CountRows {
    bool infeasible=false;
    std::map<std::pair<int,int>,double> tc,tc2;
    double constant=0;
    int thresholds=0,positive_lower=0,negative_slopes=0;
};

inline Round140CountRows round140CountRows(const std::vector<std::vector<int>>& support,
        const std::vector<double>& ratio,long long Bminus,long long B) {
    using namespace round140_detail;
    const int n=static_cast<int>(support.size())-1;
    if (n<=0 || support.size()!=ratio.size()) throw std::runtime_error("TC2 support shape");
    int exponent=0;
    long long minimum=0,maximum=0;
    for (int i=1;i<=n;++i) {
        if (support[i].empty() || ratio[i]<=0 || !std::isfinite(ratio[i]))
            throw std::runtime_error("TC2 empty support or invalid ratio");
        for (std::size_t k=0;k<support[i].size();++k)
            if (support[i][k]<0 || (k && support[i][k]<=support[i][k-1]))
                throw std::runtime_error("TC2 support must be sorted distinct nonnegative stocks");
        int e=0;std::frexp(ratio[i],&e);exponent=std::min(exponent,e-53);
        minimum+=support[i].front();maximum+=support[i].back();
    }
    Round140CountRows result;
    Bminus=std::max(Bminus,minimum);B=std::min(B,maximum);
    if (Bminus>B) {result.infeasible=true;return result;}
    std::vector<std::vector<Int>> levels(n+1);
    std::vector<Int> thresholds;
    std::map<std::pair<int,int>,Int> old,now;
    for (int i=1;i<=n;++i) {
        const Int c=units(ratio[i],exponent);
        for (int y:support[i]) {
            const Int t=mul(c,y);levels[i].push_back(t);
            if (t>0) thresholds.push_back(t);
            old[{i,y}]=now[{i,y}]=0;
        }
    }
    std::sort(thresholds.begin(),thresholds.end());
    thresholds.erase(std::unique(thresholds.begin(),thresholds.end()),thresholds.end());
    Int previous=0,constant=0;
    for (Int t:thresholds) {
        int forced=0;
        long long C0=0;
        std::vector<long long> costs,gains;
        std::vector<std::size_t> first(n+1);
        for (int i=1;i<=n;++i) {
            const auto k=std::lower_bound(levels[i].begin(),levels[i].end(),t)-levels[i].begin();
            first[i]=static_cast<std::size_t>(k);
            if (k==0) {++forced;C0+=support[i].back();}
            else if (static_cast<std::size_t>(k)==support[i].size()) C0+=support[i].back();
            else {
                costs.push_back(static_cast<long long>(support[i][k])-support[i].front());
                gains.push_back(static_cast<long long>(support[i].back())-support[i][k-1]);
                C0+=support[i][k-1];
            }
        }
        std::sort(costs.begin(),costs.end());
        std::sort(gains.rbegin(),gains.rend());
        long long used=0,total=C0;int upper=forced,q=0;
        for (long long cost:costs) {
            if (used+cost>B-minimum) break;
            used+=cost;++upper;
        }
        while (total<Bminus && q<static_cast<int>(gains.size())) total+=gains[q++];
        const int lower=forced+q;
        if (total<Bminus || lower>upper) {result.infeasible=true;return result;}
        const Int delta=t-previous;
        for (int i=1;i<=n;++i) for (std::size_t k=first[i];k<support[i].size();++k) {
            const auto key=std::make_pair(i,support[i][k]);
            old[key]=add(old[key],mul(delta,n-upper));
            now[key]=add(now[key],mul(delta,n-lower-upper));
        }
        constant=add(constant,mul(delta,static_cast<Int>(lower)*upper));
        ++result.thresholds;
        if (lower>0) ++result.positive_lower;
        if (n-lower-upper<0) ++result.negative_slopes;
        previous=t;
    }
    for (const auto& term:old) if (term.second) result.tc[term.first]=down(term.second,exponent);
    for (const auto& term:now) if (term.second) result.tc2[term.first]=down(term.second,exponent);
    result.constant=down(constant,exponent);
    return result;
}
}
