#include "FleetEventCuts.hpp"
#include <algorithm>
#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>
using namespace ebrp;
void check(bool ok,const char* message){if(!ok)throw std::runtime_error(message);}
Instance instance(int V,int M,double T,double c,std::vector<int> Q) {
    Instance in;in.V=V;in.M=M;in.Q=Q;in.total_time_limit=T;in.pickup_time=c;in.drop_time=0;
    in.initial.assign(V+1,5);in.capacity.assign(V+1,10);in.dist.assign(V+1,std::vector<double>(V+1));return in;
}
// Independent assignment enumeration, using integer zero-travel resource data.
int exhaustive(const Instance& in,const std::vector<FleetEvent>& es) {
    std::vector<int> P(in.M),D(in.M);int best=0;
    auto dfs=[&](auto&& self,int j,int count)->void {
        if(j==static_cast<int>(es.size())){best=std::max(best,count);return;}
        self(self,j+1,count);auto e=es[j];
        for(int k=0;k<in.M;++k)if(e.quantity<=in.Q[k]) {
            auto& x=e.direction<0?P[k]:D[k];x+=e.quantity;
            if((in.pickup_time+in.drop_time)*std::max(P[k],D[k])<=in.total_time_limit)self(self,j+1,count+1);
            x-=e.quantity;
        }
    };dfs(dfs,0,0);return best;
}
int main(){try {
    int cases=0;
    auto in=instance(5,2,5,2,{5,5});auto c=physicalFleetContract(in);
    std::vector<FleetEvent> es;for(int i=1;i<=5;++i)es.push_back({i,-1,1});
    check(proveFleetSmall(c,es).rank==4,"pair compatible fleet deficit");
    check(proveFleetSmall(c,{es[0],es[1]}).rank==2,"pair feasible");
    check(proveFleetLarge(c,es).rank==4,"scalable fleet deficit");
    check(!proveFleetSmall(c,{es[0],es[0]}).valid,"duplicate station");
    check(!proveFleetSmall(c,{{0,-1,1}}).valid,"invalid station");
    check(!proveFleetSmall(FleetContract{},es).valid,"unknown proof");
    in=instance(3,1,12,1,{2});c=physicalFleetContract(in);
    check(proveFleetSmall(c,{{1,-1,2},{2,1,2},{3,-1,2}}).rank==3,"pickup greater than Q remains allowed");
    check(proveFleetSmall(c,{{2,1,2}}).rank==1,"external supply allowed");
    check(proveFleetSmall(c,{{1,-1,2}}).rank==1,"loaded return allowed");
    in=instance(3,2,100,0,{1,2});c=physicalFleetContract(in);
    check(proveFleetLarge(c,{{1,-1,3},{2,1,2}}).rank==1,"zero handling eligibility");
    in=instance(3,1,10,1,{5});in.dist={{0,100,1,100},{100,0,1,1},{1,1,0,1},{100,1,1,0}};c=physicalFleetContract(in);
    check(proveFleetSmall(c,{{1,-1,1},{3,1,1}}).rank==2,"nonmetric extra shortcut");
    in=instance(2,1,2,1,{5});in.pickup_time=std::nextafter(1.0,2.0);c=physicalFleetContract(in);
    check(proveFleetSmall(c,{{1,-1,1},{2,-1,1}}).rank==2,"near boundary retained");
    in=instance(1,1,10,1,{1});in.drop_time=3*std::ldexp(1.0,-53);c=physicalFleetContract(in);
    check(c.valid&&c.handling_lower<=std::nextafter(1.0,2.0),"nonexact physical sum lower enclosure");
    FleetStatistics no_columns;
    check(separateFleetEvents(c,{},1e-5,no_columns).empty()&&no_columns.arithmetic_skips==1,"unmapped physical separator skipped");
    in.pickup_time=std::numeric_limits<double>::max();in.drop_time=in.pickup_time;
    check(!physicalFleetContract(in).valid,"nominal handling overflow rejected");
    in=instance(1,1,100,1,{1});in.initial[1]=in.capacity[1]=std::numeric_limits<int>::max();
    NativeOtB1LinearModel edge;
    edge.names={"Y_1","state_1_2147483647","p_0_1","d_0_1","z_0_1","mode_0_1","ord_0_1","x_0_0_1","x_0_1_0"};
    edge.types={'I','B','I','I','B','B','C','B','B'};
    const double imax=std::numeric_limits<int>::max();
    edge.lower_bounds={imax,0,0,0,0,0,0,0,0};edge.upper_bounds={imax,1,1,0,1,1,1,1,1};edge.row_starts={0};
    auto add=[&](char sense,double rhs,std::initializer_list<std::pair<int,double>> a) {
        edge.senses.push_back(sense);edge.rhs.push_back(rhs);
        for(auto [j,v]:a){edge.column_indices.push_back(j);edge.coefficients.push_back(v);}
        edge.row_starts.push_back(static_cast<int>(edge.coefficients.size()));
    };
    add('=',1,{{1,1}});add('=',0,{{0,1},{1,-imax}});
    add('<',0,{{5,1},{4,-1}});add('<',0,{{2,1},{5,-1}});add('<',0,{{3,1}});
    add('>',0,{{2,1},{3,1},{4,-1}});add('=',imax,{{0,1},{2,1},{3,-1}});add('<',1,{{4,1}});
    add('=',0,{{8,1},{4,-1}});add('=',0,{{7,1},{4,-1}});
    add('<',1,{{7,1}});add('=',0,{{7,1},{8,-1}});add('>',0,{{2,1},{3,-1}});add('<',100,{{2,1}});
    check(prepareFleetContract(in,edge).valid,"fixed INT_MAX inventory endpoint audit");
    for(int M=1;M<=3;++M)for(int T=0;T<=6;++T)for(int cost=0;cost<=3;++cost)for(int pattern=0;pattern<64;++pattern) {
        in=instance(3,M,T,cost,M==1?std::vector<int>{1}:M==2?std::vector<int>{1,3}:std::vector<int>{1,2,3});
        es.clear();for(int i=1;i<=3;++i)es.push_back({i,(pattern&(1<<(i-1)))?1:-1,1+((pattern>>(i+2))&1)});
        const int expected=exhaustive(in,es);c=physicalFleetContract(in);
        auto small=proveFleetSmall(c,es),large=proveFleetLarge(c,es),sum=proveFleetLarge(c,es,false);
        check(small.valid&&large.valid&&sum.valid,"proof validity");
        check(small.rank==expected,"complete DP vs independent enumeration");
        check(large.rank>=expected&&sum.rank>=large.rank,"upper direction and Hall dominance");++cases;
    }
    std::cout<<"PASS independent assignment cases="<<cases<<"; physical edge fixtures passed; Optimize=0\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
