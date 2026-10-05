#include "ServiceResourceCuts.hpp"
#include <iostream>
#include <functional>
#include <limits>
#include <cmath>
#include <stdexcept>
using namespace ebrp;
void check(bool ok,const char*s){if(!ok)throw std::runtime_error(s);}
Instance fixture(int n,int Q,int T,int c){Instance in;in.V=n;in.M=1;in.Q={Q};in.total_time_limit=T;in.pickup_time=c;in.drop_time=0;
    in.initial.assign(n+1,2);in.capacity.assign(n+1,4);in.dist.assign(n+1,std::vector<double>(n+1));return in;}
long long enumerate(const Instance&in,const std::vector<ServiceWeight>&w){long long best=0;
    std::function<void(int,int,int,long long)> dfs=[&](int i,int p,int d,long long value){
        if(i>in.V){if(d<=p&&in.pickup_time*p<=in.total_time_limit)best=std::max(best,value);return;}
        dfs(i+1,p,d,value);
        for(int a=1;a<=std::min(in.initial[i],in.Q[0]);++a)dfs(i+1,p+a,d,value+w[i][0]*a+w[i][2]);
        for(int b=1;b<=std::min(in.capacity[i]-in.initial[i],in.Q[0]);++b)dfs(i+1,p,d+b,value+w[i][1]*b+w[i][2]);
    };dfs(1,0,0,0);return best;}
int main(){try{int cases=0;
    for(int Q=0;Q<=3;++Q)for(int T=0;T<=8;++T)for(int cost=0;cost<=3;++cost)for(int seed=0;seed<12;++seed){
        auto in=fixture(4,Q,T,cost);std::vector<ServiceWeight>w(5,{0,0,0});
        for(int i=1;i<=4;++i)w[i]={((seed+i*3)%7)-3,((seed*2+i)%7)-3,((seed*3+i*2)%9)-4};
        auto r=proveServiceSupport(physicalFleetContract(in),0,w);check(r.valid,"fixture support validity");
        check(r.upper==enumerate(in,w),"complete signed maximum differs from independent enumeration");++cases;
    }
    auto in=fixture(3,2,4,1);in.initial={0,2,0,2};in.capacity={0,2,2,2};
    std::vector<ServiceWeight>w(4,{0,0,0});w[2]={0,10,0};
    check(proveServiceSupport(physicalFleetContract(in),0,w).upper==20,"outside zero-profit supplier");
    w[1]={10,0,0};w[2]={0,0,0};w[3]={10,0,0};
    check(proveServiceSupport(physicalFleetContract(in),0,w).upper==40,"cumulative pickup exceeds Q");
    auto c=physicalFleetContract(in);w[1][0]=std::numeric_limits<long long>::min();
    check(!proveServiceSupport(c,0,w).valid,"LLONG_MIN rejected before abs");
    w[1][0]=1;check(!proveServiceSupport(c,2,w).valid,"invalid vehicle");
    c.handling_lower=std::numeric_limits<double>::quiet_NaN();check(!proveServiceSupport(c,0,w).valid,"nonfinite coefficient");
    in=fixture(3,1000,10000,0);in.initial.assign(4,1000);in.capacity.assign(4,2000);w.assign(4,{1,0,0});
    check(!proveServiceSupport(physicalFleetContract(in),0,w).valid,"unsupported dimension emits no RHS");
    in=fixture(2,2,2,1);in.pickup_time=std::nextafter(1.0,2.0);w.assign(3,{1,0,0});
    check(proveServiceSupport(physicalFleetContract(in),0,w).upper==2,"boundary retained outward");
    std::cout<<"passed "<<cases<<" signed necessary-system enumeration cases plus boundary fixtures; Optimize=0\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
