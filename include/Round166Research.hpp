#pragma once
#include <algorithm>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace ebrp {
// Explicit, default-off research identity. No data- or clock-based selection.
inline bool& round166Breakpoint() { static bool enabled=false; return enabled; }
inline std::vector<int> round166Support(int lower,int upper,int initial) {
    if(lower>upper)return {};
    std::vector<int> support{lower,upper};
    for(long long a=static_cast<long long>(initial)-1;a<=static_cast<long long>(initial)+1;++a)
        if(a>=lower&&a<=upper)support.push_back(static_cast<int>(a));
    std::sort(support.begin(),support.end());
    support.erase(std::unique(support.begin(),support.end()),support.end());
    return support;
}
inline std::string round166T(int i,int a) {return "r166_t_"+std::to_string(i)+"_"+std::to_string(a);}
inline std::string round166Q(int i,int a) {return "r166_q_"+std::to_string(i)+"_"+std::to_string(a);}
inline std::vector<std::pair<int,double>> round166Weights(const std::vector<int>& support,int y) {
    if(support.empty()||y<support.front()||y>support.back())throw std::runtime_error("round166_start_outside_support");
    const auto hi=std::lower_bound(support.begin(),support.end(),y);
    if(hi!=support.end()&&*hi==y)return {{y,1.0}};
    const int a=*(hi-1),b=*hi;
    return {{a,static_cast<double>(b-y)/(b-a)},{b,static_cast<double>(y-a)/(b-a)}};
}
} // namespace ebrp
