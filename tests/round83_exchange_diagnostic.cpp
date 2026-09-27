#include "Round83BlockExchange.hpp"
#include "Parser.hpp"
#include "Evaluator.hpp"
#include "ProcessPhaseLedger.hpp"
#include <algorithm>
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>
#include <tuple>
using namespace ebrp;
void require(bool x,const char* why){if(!x)throw std::runtime_error(why);}
auto key(const Round83Choice& c){return std::make_tuple(c.kind,c.source,c.first,c.last,c.target,c.target_first,c.target_last);}
std::vector<double> potential(const Verification& v){auto d=v.route_duration;std::sort(d.begin(),d.end(),std::greater<double>());return d;}
// Independent full reconstruction, not the production splice/materializer or prefix cache.
std::vector<RoutePlan> oracleMove(const std::vector<RoutePlan>& routes,const Round83Choice& c) {
    std::map<int,std::vector<int>> seq;std::map<int,StopOperation> ops;
    for(const auto& r:routes){seq[r.vehicle]={r.nodes.begin()+1,r.nodes.end()-1};for(const auto& op:r.operations)ops[op.station]=op;}
    const auto a=seq.at(c.source),b=seq[c.target];
    std::vector<int> x(a.begin()+c.first,a.begin()+c.last),y(b.begin()+c.target_first,b.begin()+c.target_last);
    std::vector<int> na,nb;
    for(int j=0;j<=static_cast<int>(a.size());++j){if(j==c.first)na.insert(na.end(),y.begin(),y.end());if(j<static_cast<int>(a.size())&&(j<c.first||j>=c.last))na.push_back(a[j]);}
    for(int j=0;j<=static_cast<int>(b.size());++j){if(j==c.target_first)nb.insert(nb.end(),x.begin(),x.end());if(j<static_cast<int>(b.size())&&(j<c.target_first||j>=c.target_last))nb.push_back(b[j]);}
    seq[c.source]=na;seq[c.target]=nb;std::vector<RoutePlan> out;
    for(const auto& kv:seq)if(!kv.second.empty()){
        RoutePlan r;r.vehicle=kv.first;r.nodes={0};for(int i:kv.second){r.nodes.push_back(i);r.operations.push_back(ops.at(i));}r.nodes.push_back(0);out.push_back(r);
    }return out;
}
Round83Choice oracle(const Instance& in,const std::vector<RoutePlan>& routes,std::ostream& log,const char* name) {
    auto initial=verifySolution(in,routes,.15);require(initial.feasible&&initial.errors.empty(),"Invalid oracle fixture");
    std::vector<std::vector<int>> nodes(in.M);std::map<int,int> op;
    for(const auto& r:routes){nodes[r.vehicle]={r.nodes.begin()+1,r.nodes.end()-1};for(const auto& o:r.operations)op[o.station]=o.pickup-o.drop;}
    Round83Choice brute;std::uint64_t blocks=0,count[2]={0,0},feasible[2]={0,0},improving[2]={0,0};
    auto check=[&](Round83Choice c){
        ++count[c.kind];auto v=verifySolution(in,oracleMove(routes,c),.15);
        if(!v.feasible||!v.errors.empty())return;
        ++feasible[c.kind];require(v.final_inventory==initial.final_inventory&&v.objective==initial.objective,"Oracle changed inventory/F");
        c.duration_potential=potential(v);if(!(c.duration_potential<potential(initial)))return;
        ++improving[c.kind];if(!brute.found||c.duration_potential<brute.duration_potential||
            (c.duration_potential==brute.duration_potential&&key(c)<key(brute)))brute=c;
    };
    for(int s=0;s<in.M;++s)for(int f=0;f<static_cast<int>(nodes[s].size());++f)
      for(int l=f+1;l<=static_cast<int>(nodes[s].size());++l){
        int net=0;for(int j=f;j<l;++j)net+=op.at(nodes[s][j]);
        if(!net){++blocks;for(int t=0;t<in.M;++t)if(t!=s)for(int leg=0;leg<=static_cast<int>(nodes[t].size());++leg)
            check({true,0,s,f,l,t,leg,leg,{}});}
        for(int t=s+1;t<in.M;++t)for(int tf=0;tf<static_cast<int>(nodes[t].size());++tf)
          for(int tl=tf+1;tl<=static_cast<int>(nodes[t].size());++tl){
            int other=0;for(int j=tf;j<tl;++j)other+=op.at(nodes[t][j]);
            if(other==net)check({true,1,s,f,l,t,tf,tl,{}});
          }
      }
    Round83Stats stats;auto actual=bestRound83Neutral(in,routes,.15,stats);
    require(!stats.deadline&&stats.relocation.balanced_blocks==blocks&&stats.relocation.placements==count[0]&&
        stats.relocation.feasible_placements==feasible[0]&&stats.relocation.improving_placements==improving[0]&&
        stats.equal_net_pairs==count[1]&&stats.feasible==feasible[1]&&stats.improving==improving[1],"Oracle enumeration count mismatch");
    require(actual.found==brute.found,"Oracle existence mismatch");
    if(actual.found){
        require(key(actual)==key(brute)&&actual.duration_potential==brute.duration_potential,"Oracle best tuple/key mismatch");
        auto v=verifySolution(in,applyRound83Neutral(routes,actual),.15);
        require(v.feasible&&v.errors.empty()&&v.final_inventory==initial.final_inventory&&v.objective==initial.objective&&potential(v)==actual.duration_potential,"Selected materialization mismatch");
    }
    Round83Stats againStats;auto again=bestRound83Neutral(in,routes,.15,againStats);
    require(again.found==actual.found&&key(again)==key(actual)&&again.duration_potential==actual.duration_potential,"Nondeterministic selection");
    log<<"{\"case\":\""<<name<<"\",\"relocations\":"<<count[0]<<",\"exchange_pairs\":"<<count[1]
       <<",\"exchange_feasible\":"<<feasible[1]<<",\"exchange_improving\":"<<improving[1]
       <<",\"selected_kind\":"<<actual.kind<<",\"found\":"<<(actual.found?"true":"false")<<",\"passed\":true}\n";
    return actual;
}
void structural(const std::filesystem::path& out){
    Instance in;in.V=7;in.M=3;in.Q={3,3,3};in.capacity.assign(8,10);in.initial.assign(8,5);
    in.target.assign(8,5);in.weights.assign(8,1);in.weights[0]=0;in.pickup_time=1;in.drop_time=2;in.total_time_limit=100;
    in.dist.assign(8,std::vector<double>(8,1));for(int i=0;i<=7;++i)in.dist[i][i]=0;
    std::vector<RoutePlan> routes={{0,{0,1,2,3,4,0},{{1,3,0},{2,0,2},{3,2,0},{4,0,3}}},
        {1,{0,5,6,0},{{5,2,0},{6,0,2}}}};
    std::ofstream log(out/"structural.jsonl");
    oracle(in,routes,log,"negative_relative_prefix_and_ties");
    auto h=in;h.Q={3,2,1};oracle(h,routes,log,"heterogeneous_Q");
    auto loaded=routes;loaded[0].nodes.insert(loaded[0].nodes.end()-1,7);loaded[0].operations.push_back({7,1,0});
    oracle(in,loaded,log,"loaded_return");
    auto nonmetric=in;nonmetric.dist[1][4]=40;nonmetric.total_time_limit=30;oracle(nonmetric,routes,log,"nonmetric_duration");
    auto boundary=in;boundary.total_time_limit=20;oracle(boundary,routes,log,"exact_T_boundary");
    auto whole=in;whole.dist[0][1]=whole.dist[1][0]=20;
    oracle(whole,{{0,{0,1,2,0},{{1,2,0},{2,0,2}}},{1,{0,5,6,0},{{5,2,0},{6,0,2}}}},log,"unused_vehicle_and_deletion");
    oracle(in,{},log,"empty_routes");
    auto crossed=in;crossed.pickup_time=0;crossed.drop_time=0;
    crossed.dist.assign(8,std::vector<double>(8,10));for(int i=0;i<8;++i)crossed.dist[i][i]=0;
    crossed.dist[1][2]=crossed.dist[3][4]=20;crossed.dist[1][4]=crossed.dist[3][2]=1;
    std::vector<RoutePlan> cr={{0,{0,1,2,0},{{1,2,0},{2,0,2}}},{1,{0,3,4,0},{{3,2,0},{4,0,2}}}};
    auto chosen=oracle(crossed,cr,log,"nonzero_net_beneficial_exchange");
    require(chosen.found&&chosen.kind==1,"Nonzero exchange fixture did not select exchange");
    // Explicitly reject unequal-net exchange; a materializer must not hide an invalid selector.
    bool rejected=false;try{applyRound83Neutral(cr,{true,1,0,0,1,1,1,2,{}});}catch(const std::invalid_argument&){rejected=true;}
    require(rejected,"Unequal-net materialization accepted");
    SolveOptions expired;expired.process_start_time_valid=true;expired.process_start_time=std::chrono::steady_clock::now()-std::chrono::seconds(2);
    expired.process_wall_time_limit=1;expired.process_shutdown_margin_seconds=0;
    Round83Stats es;auto no=bestRound83Neutral(in,routes,.15,es,&expired);require(es.deadline&&!no.found&&es.equal_net_pairs==0,"Whole deadline failed");
    auto invalid=routes;invalid[0].operations[0].pickup=4;rejected=false;
    try{Round83Stats s;bestRound83Neutral(in,invalid,.15,s);}catch(const std::invalid_argument&){rejected=true;}require(rejected,"Invalid input accepted");
    auto zero=in;for(const auto& r:routes)for(const auto& op:r.operations)zero.target[op.station]=zero.initial[op.station]-op.pickup+op.drop;
    SolveOptions opt;opt.lambda=.15;auto z=runRound83ExchangeDescent(zero,opt,routes,out/"zero");require(z.zero&&z.neutral==0,"Zero objective did not stop");
    auto d=runRound83ExchangeDescent(in,expired,routes,out/"deadline");require(d.deadline&&d.neutral==0,"Descent whole deadline failed");
    std::ofstream summary(out/"result.json");summary<<"{\"passed\":true,\"oracle_cases\":8,\"deadline_zero_invalid_checks\":true,\"optimizer_calls\":0}\n";
}
int main(int argc,char** argv){
    try{
        SolveOptions opt;opt.process_start_time_valid=true;opt.process_start_time=std::chrono::steady_clock::now();opt.process_wall_time_limit=120;opt.process_shutdown_margin_seconds=1;
        if(argc==3&&std::string(argv[1])=="structural"){structural(argv[2]);return 0;}
        require(argc==9&&std::string(argv[1])=="fixed","Invalid diagnostic command");
        auto in=parseInstanceFile(argv[2],std::stod(argv[3]),std::stod(argv[4]),std::stod(argv[5]));opt.lambda=std::stod(argv[6]);
        std::ifstream input(argv[7]);int count=0;input>>count;require(bool(input)&&count>=0,"Invalid route count");std::vector<RoutePlan> routes;
        for(int k=0;k<count;++k){RoutePlan r;int n;input>>r.vehicle>>n;require(n>=0,"Invalid station count");r.nodes={0};
            for(int j=0;j<n;++j){StopOperation op;input>>op.station>>op.pickup>>op.drop;r.nodes.push_back(op.station);r.operations.push_back(op);}r.nodes.push_back(0);routes.push_back(r);}
        require(bool(input),"Invalid frozen route input");auto r=runRound83ExchangeDescent(in,opt,routes,argv[8]);
        require(!r.verification_failed,"Physical exchange adoption failed");return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
