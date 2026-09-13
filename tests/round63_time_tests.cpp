#include "Round63TimeResource.hpp"
#include "FileSha256.hpp"
#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <numeric>
#include <random>
#include <stdexcept>

namespace {
void require(bool b,const char* msg){if(!b)throw std::runtime_error(msg);}
ebrp::Instance toy(int n) {
    ebrp::Instance in;in.V=n;in.M=2;in.Q={2,4};in.initial.assign(n+1,5);in.capacity.assign(n+1,10);
    in.target.assign(n+1,5);in.pickup_time=.3;in.drop_time=.7;in.total_time_limit=50;
    in.dist.assign(n+1,std::vector<double>(n+1));
    for(int i=0;i<=n;++i)for(int j=0;j<=n;++j)if(i!=j)in.dist[i][j]=(i*19+j*7)%17; // directed, nonmetric, zero arcs
    return in;
}
std::vector<int> subset(int n,int mask){std::vector<int>s;for(int i=1;i<=n;++i)if(mask&(1<<(i-1)))s.push_back(i);return s;}
void routes() {
    auto in=toy(4);std::vector<int> order={1,2,3,4};long long checked=0;bool over_capacity_total=false,loaded_return=false;
    do {
        for(int mask=0;mask<256;++mask)for(int k=0;k<2;++k) {
            int tmp=mask,load=0,pickups=0;bool feasible=true;std::vector<int> op;
            for(int i:order){(void)i;int q=(tmp%4<2?tmp%4-2:tmp%4-1);tmp/=4;op.push_back(q);load+=q;pickups+=std::max(0,q);if(load<0||load>in.Q[k])feasible=false;}
            if(!feasible)continue;
            double travel=in.dist[0][order[0]]+in.dist[order.back()][0];
            for(int t=1;t<4;++t)travel+=in.dist[order[t-1]][order[t]];
            in.total_time_limit=travel+(in.pickup_time+in.drop_time)*pickups;
            auto d=ebrp::prepareRound63Time(in);auto p=ebrp::emptyRound63TimePoint(d);int last=0;double prepaid=0;
            for(int t=0;t<4;++t) {
                int i=order[t];p.x[k][last][i]=1;p.pickup[k][i]=std::max(0,op[t]);
                prepaid+=d.travel[last][i]+d.handling*p.pickup[k][i];int next=t==3?0:order[t+1];
                require(prepaid<=d.upper[i][next]+1e-12,"canonical cumulative f exceeds capacity");last=i;
            }
            p.x[k][last][0]=1;
            for(int w=1;w<16;++w){auto r=ebrp::round63TimeRow(d,k,subset(4,w));require(ebrp::evaluateRound63TimeRow(d,p,r)<1e-11,"legal route cut off");}
            require(!ebrp::separateRound63Time(d,p,k).violated,"legal route separated");
            over_capacity_total|=pickups>in.Q[k];loaded_return|=load>0;++checked;
        }
    } while(std::next_permutation(order.begin(),order.end()));
    require(checked>100&&over_capacity_total&&loaded_return,"route coverage missing");
}
void fractions() {
    std::mt19937 rng(631);std::uniform_real_distribution<double> u(0,1);bool proper=false,single=false,full=false;
    for(int iteration=0;iteration<240;++iteration) {
        auto in=toy(2+iteration%5);in.total_time_limit=10+iteration%71;auto d=ebrp::prepareRound63Time(in);auto p=ebrp::emptyRound63TimePoint(d);
        for(int k=0;k<d.M;++k)for(int i=0;i<=d.V;++i) {p.pickup[k][i]=u(rng)*3;for(int j=0;j<=d.V;++j)if(i!=j)p.x[k][i][j]=u(rng);}
        for(int k=0;k<d.M;++k) {
            double best=0;
            for(int w=1;w<(1<<d.V);++w){auto r=ebrp::round63TimeRow(d,k,subset(d.V,w));best=std::max(best,ebrp::evaluateRound63TimeRow(d,p,r));}
            const auto r=ebrp::separateRound63Time(d,p,k);
            require(std::fabs(r.violation-best)<2e-10,"mincut differs from exhaustive raw violation");
            require(std::fabs(r.source_capacity-r.mincut-best)<2e-10,"flow cut identity");
            proper|=r.support.size()>1&&r.support.size()<static_cast<std::size_t>(d.V);single|=r.support.size()==1;full|=r.support.size()==static_cast<std::size_t>(d.V);
            std::set<std::string> seen;
            if(r.violated){require(ebrp::acceptRound63TimeCut(d,r,seen),"cut acceptance");require(!ebrp::acceptRound63TimeCut(d,r,seen),"duplicate accepted");}
        }
    }
    require(proper&&single&&full,"support classes missing");
}
void boundaries() {
    auto in=toy(3);in.total_time_limit=0;in.pickup_time=in.drop_time=0;for(auto& r:in.dist)std::fill(r.begin(),r.end(),0);
    auto d=ebrp::prepareRound63Time(in);auto p=ebrp::emptyRound63TimePoint(d);
    require(!ebrp::separateRound63Time(d,p,0).violated,"empty zero resource");
    p.x[0][0][1]=p.x[0][1][0]=1;p.pickup[0][1]=2;require(!ebrp::separateRound63Time(d,p,0).violated,"zero resource loaded return");
    p.x[0][1][2]=-1e-10;require(!ebrp::separateRound63Time(d,p,0).violated,"tiny clipping");
    p.x[0][1][2]=-1e-3;bool failed=false;try{ebrp::separateRound63Time(d,p,0);}catch(...){failed=true;}require(failed,"invalid point accepted");
    auto cut=ebrp::round63TimeRow(d,0,{1,3});cut.scope="local";std::set<std::string>s;
    failed=false;try{ebrp::acceptRound63TimeCut(d,cut,s);}catch(...){failed=true;}require(failed,"local cut accepted");
    cut=ebrp::round63TimeRow(d,0,{1});in.total_time_limit=2;auto other=ebrp::prepareRound63Time(in);
    failed=false;try{ebrp::acceptRound63TimeCut(other,cut,s);}catch(...){failed=true;}require(failed,"cross T reuse");
    auto path=std::filesystem::temp_directory_path()/"round63_default_off_test.lp";
    {std::ofstream o(path);o<<"unaltered model bytes\n";}auto hash=ebrp::fileSha256(path);
    ebrp::appendRound63TimeModel(in,path,"off");require(ebrp::fileSha256(path)==hash,"default off modifies model");std::filesystem::remove(path);
    require(ebrp::SolveOptions{}.round63_time_mode=="off","default not off");
}
}
int main(){try{routes();fractions();boundaries();std::cout<<"Round63 route/subset enumeration, mincut, numerical and scope checks passed\n";return 0;}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
