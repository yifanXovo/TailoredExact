#include "Round78BalancedRelocation.hpp"
#include "Round76PhysicalClosure.hpp"
#include "Round61Candidates.hpp"
#include "Parser.hpp"
#include "Evaluator.hpp"
#include "ProcessPhaseLedger.hpp"
#include <algorithm>
#include <chrono>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <stdexcept>
#include <tuple>
using namespace ebrp;

void require(bool condition, const char* why) { if (!condition) throw std::runtime_error(why); }
void snapshot(const std::filesystem::path& path, const Instance& in, double lambda,
              const std::vector<RoutePlan>& routes) {
    VerifiedCandidateStore store;
    require(store.consider(in, lambda, routes, "round78_fixed_diagnostic", "original_problem"), "snapshot failed");
    writeRound61Witness(path, in, lambda, store.best());
}
auto moveKey(const Round78BlockChoice& c) { return std::make_tuple(c.source,c.first,c.last,c.target,c.leg); }
std::vector<double> oraclePotential(const Verification& v) {
    auto p=v.route_duration;std::sort(p.begin(),p.end(),std::greater<double>());return p;
}
// Independent whole materialization: reconstruct all routes from station lists,
// then use the original verifier on every candidate. No production apply/cache.
std::vector<RoutePlan> oracleMove(const std::vector<RoutePlan>& routes, const Round78BlockChoice& c) {
    std::map<int,std::vector<int>> nodes;
    std::map<int,StopOperation> ops;
    for(const auto& r:routes) {
        nodes[r.vehicle]={r.nodes.begin()+1,r.nodes.end()-1};
        for(const auto& op:r.operations)ops[op.station]=op;
    }
    auto a=nodes.at(c.source);auto b=nodes[c.target];
    std::vector<int> block(a.begin()+c.first,a.begin()+c.last), remaining;
    for(int i=0;i<static_cast<int>(a.size());++i)if(i<c.first||i>=c.last)remaining.push_back(a[i]);
    std::vector<int> target;
    for(int i=0;i<=static_cast<int>(b.size());++i) {
        if(i==c.leg)target.insert(target.end(),block.begin(),block.end());
        if(i<static_cast<int>(b.size()))target.push_back(b[i]);
    }
    nodes[c.source]=remaining;nodes[c.target]=target;
    std::vector<RoutePlan> out;
    for(const auto& item:nodes)if(!item.second.empty()) {
        RoutePlan r;r.vehicle=item.first;r.nodes={0};
        for(int i:item.second){r.nodes.push_back(i);r.operations.push_back(ops.at(i));}
        r.nodes.push_back(0);out.push_back(r);
    }
    return out;
}
void oracle(const Instance& in,const std::vector<RoutePlan>& routes,std::ostream& log,const char* name) {
    auto initial=verifySolution(in,routes,.15);require(initial.feasible&&initial.errors.empty(),"invalid oracle fixture");
    auto potential=oraclePotential(initial);
    std::vector<std::vector<int>> nodes(in.M);std::map<int,int> signed_op;
    for(const auto& r:routes) {
        nodes[r.vehicle]={r.nodes.begin()+1,r.nodes.end()-1};
        for(const auto& op:r.operations)signed_op[op.station]=op.pickup-op.drop;
    }
    Round78BlockChoice brute;std::uint64_t feasible=0, placements=0,balanced=0,improving=0;
    for(int s=0;s<in.M;++s)for(int a=0;a<static_cast<int>(nodes[s].size());++a)
      for(int b=a+1;b<=static_cast<int>(nodes[s].size());++b) {
        int net=0;for(int j=a;j<b;++j)net+=signed_op.at(nodes[s][j]);
        if(net)continue;++balanced;
        for(int t=0;t<in.M;++t)if(t!=s)for(int leg=0;leg<=static_cast<int>(nodes[t].size());++leg) {
            ++placements;Round78BlockChoice c{true,s,a,b,t,leg,{}};
            auto next=oracleMove(routes,c);auto checked=verifySolution(in,next,.15);
            if(!checked.feasible||!checked.errors.empty())continue;
            ++feasible;require(checked.final_inventory==initial.final_inventory,"oracle inventory changed");
            require(checked.objective==initial.objective,"oracle F changed");
            c.duration_potential=oraclePotential(checked);
            if(!(c.duration_potential<potential))continue;++improving;
            if(!brute.found||c.duration_potential<brute.duration_potential||
                (c.duration_potential==brute.duration_potential&&moveKey(c)<moveKey(brute)))brute=c;
        }
      }
    Round78BlockStats stats;auto actual=bestRound78BalancedRelocation(in,routes,.15,stats);
    require(stats.placements==placements&&stats.balanced_blocks==balanced&&
        stats.feasible_placements==feasible&&stats.improving_placements==improving,"oracle count mismatch");
    require(actual.found==brute.found,"oracle existence mismatch");
    if(actual.found) {
        require(moveKey(actual)==moveKey(brute)&&actual.duration_potential==brute.duration_potential,"oracle best mismatch");
        auto checked=verifySolution(in,applyRound78BalancedRelocation(routes,actual),.15);
        require(checked.feasible&&checked.errors.empty()&&checked.final_inventory==initial.final_inventory&&
            oraclePotential(checked)==actual.duration_potential,"selected materialization mismatch");
    }
    Round78BlockStats repeat;auto again=bestRound78BalancedRelocation(in,routes,.15,repeat);
    require(again.found==actual.found&&moveKey(again)==moveKey(actual)&&again.duration_potential==actual.duration_potential,"nondeterminism");
    log<<"{\"case\":\""<<name<<"\",\"placements\":"<<placements<<",\"feasible\":"<<feasible
       <<",\"improving\":"<<improving<<",\"found\":"<<(actual.found?"true":"false")<<",\"passed\":true}\n";
}


void structural(const std::filesystem::path& out) {
    Instance in;in.V=7;in.M=3;in.Q={3,3,3};in.capacity.assign(8,10);in.initial.assign(8,5);
    in.target.assign(8,5);in.weights.assign(8,1);in.weights[0]=0;
    in.pickup_time=1;in.drop_time=2;in.total_time_limit=100;
    in.dist.assign(8,std::vector<double>(8,1));for(int i=0;i<=7;++i)in.dist[i][i]=0;
    std::vector<RoutePlan> routes={{0,{0,1,2,3,4,0},{{1,3,0},{2,0,2},{3,2,0},{4,0,3}}},
        {1,{0,5,6,0},{{5,2,0},{6,0,2}}}};
    std::ofstream log(out/"structural.jsonl");oracle(in,routes,log,"negative_relative_prefix");
    Round78BlockChoice negative{true,0,1,3,2,0,{}};
    require(!verifySolution(in,oracleMove(routes,negative),.15).feasible,"negative block accepted on empty target");
    negative.target=1;negative.leg=1;
    require(verifySolution(in,oracleMove(routes,negative),.15).feasible,"negative block rejected at positive entry load");
    auto heterogeneous=in;heterogeneous.Q={3,2,1};oracle(heterogeneous,routes,log,"heterogeneous_Q");
    auto loaded=routes;loaded[0].nodes.insert(loaded[0].nodes.end()-1,7);loaded[0].operations.push_back({7,1,0});
    oracle(in,loaded,log,"loaded_return");
    auto nonmetric=in;nonmetric.dist[1][4]=40;nonmetric.total_time_limit=30;
    oracle(nonmetric,routes,log,"nonmetric_source_shortcut");
    auto boundary=in;boundary.total_time_limit=20;oracle(boundary,routes,log,"exact_T_boundary");
    auto whole=in;whole.dist[0][1]=whole.dist[1][0]=20;
    oracle(whole,{{0,{0,1,2,0},{{1,2,0},{2,0,2}}},{1,{0,5,6,0},{{5,2,0},{6,0,2}}}},log,"source_route_deletion");
    oracle(in,{},log,"empty_routes");
    SolveOptions expired;expired.process_start_time_valid=true;
    expired.process_start_time=std::chrono::steady_clock::now()-std::chrono::seconds(2);
    expired.process_wall_time_limit=1;expired.process_shutdown_margin_seconds=0;
    Round78BlockStats stats;auto move=bestRound78BalancedRelocation(in,routes,.15,stats,&expired);
    require(stats.deadline_reached&&!move.found&&stats.placements==0,"deadline failed");
    auto zero=in;for(const auto& r:routes)for(const auto& op:r.operations)zero.target[op.station]=zero.initial[op.station]-op.pickup+op.drop;
    SolveOptions opt;opt.lambda=.15;std::filesystem::create_directory(out/"zero");
    auto z=runRound78BalancedDescent(zero,opt,routes,out/"zero");require(z.zero&&z.neutral==0&&z.insertions==0&&z.quantities==0,"zero did not stop");
    std::filesystem::create_directory(out/"deadline");auto d=runRound78BalancedDescent(in,expired,routes,out/"deadline");
    require(d.deadline&&d.neutral==0,"whole descent deadline failed");
    auto invalid=routes;invalid[0].operations[0].pickup=4;bool rejected=false;
    try{Round78BlockStats s;bestRound78BalancedRelocation(in,invalid,.15,s);}catch(const std::invalid_argument&){rejected=true;}
    require(rejected,"invalid physical input accepted");
    std::vector<double> earlier_increase{10+1e-13,2},old{10,3};require(!(earlier_increase<old),"lex order ignored earlier increase");
    Instance mixed; mixed.V=4;mixed.M=2;mixed.Q={5,5};mixed.capacity={0,5,5,5,5};
    mixed.initial={0,5,0,5,0};mixed.target={1,1,4,1,4};mixed.weights={0,1,1,1,1};
    mixed.dist.assign(5,std::vector<double>(5,0));mixed.pickup_time=1;mixed.drop_time=1;mixed.total_time_limit=5;
    std::vector<RoutePlan> mr={{0,{0,1,2,3,4,0},{{1,1,0},{2,0,1},{3,1,0},{4,0,1}}}};
    std::filesystem::create_directory(out/"mixed");
    auto initial_mixed=verifySolution(mixed,mr,.15);
    auto m=runRound78BalancedDescent(mixed,opt,mr,out/"mixed");
    require(m.exhausted&&!m.verification_failed&&m.neutral>=1&&m.quantities>=1&&
        m.verification.objective<initial_mixed.objective,"actual neutral/strict composition not exercised");
    std::ofstream summary(out/"result.json");summary<<"{\"passed\":true,\"oracle_cases\":7,\"deadline_zero_invalid_checks\":true,\"optimizer_calls\":0}\n";
}

int main(int argc,char** argv) {
    try {
        SolveOptions opt;opt.process_start_time_valid=true;opt.process_start_time=std::chrono::steady_clock::now();
        opt.process_wall_time_limit=60;opt.process_shutdown_margin_seconds=1;
        if(argc==3&&std::string(argv[1])=="structural") {structural(argv[2]);return 0;}
        require(argc==9&&std::string(argv[1])=="fixed","invalid diagnostic command");
        auto in=parseInstanceFile(argv[2],std::stod(argv[3]),std::stod(argv[4]),std::stod(argv[5]));opt.lambda=std::stod(argv[6]);
        std::ifstream input(argv[7]);int count=0;input>>count;require(bool(input)&&count>=0,"invalid route count");std::vector<RoutePlan> routes;
        for(int k=0;k<count;++k){RoutePlan r;int n;input>>r.vehicle>>n;r.nodes={0};
            for(int j=0;j<n;++j){StopOperation op;input>>op.station>>op.pickup>>op.drop;r.nodes.push_back(op.station);r.operations.push_back(op);}
            r.nodes.push_back(0);routes.push_back(r);}
        require(bool(input),"invalid frozen route input");
        runRound78BalancedDescent(in,opt,routes,argv[8]);return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
