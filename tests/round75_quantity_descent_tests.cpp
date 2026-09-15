#include "Round75QuantityDescent.hpp"
#include "Evaluator.hpp"
#include "Round60Candidates.hpp"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <iostream>
#include <map>
#include <stdexcept>

using namespace ebrp;
static void require(bool ok, const char* reason) { if (!ok) throw std::runtime_error(reason); }
static std::vector<RoutePlan> seed() {
    return {{0,{0,3,1,4,2,0},{{3,2,0},{1,0,1},{4,2,0},{2,0,1}}},
            {1,{0,7,5,8,6,0},{{7,3,0},{5,0,2},{8,1,0},{6,0,1}}}};
}
static Instance fixture(int variant) {
    Instance in; in.V=8; in.M=3; in.Q={3,4,1};
    in.initial={0,1,0,4,3,1,0,4,3}; in.capacity.assign(9,6);
    in.target.resize(9); in.weights.assign(9,.125); in.weights[0]=0;
    for(int i=1;i<=8;++i) in.target[i]=1+(i+variant)%4;
    in.pickup_time=variant%3==0?0:.13;
    in.drop_time=variant%3==0?0:.37;
    in.total_time_limit=10000;
    in.dist.assign(9,std::vector<double>(9));
    for(int i=0;i<=8;++i) for(int j=0;j<=8;++j) if(i!=j) {
        // Deliberately asymmetric/nonmetric cases: deleting stops may increase travel.
        in.dist[i][j]=variant%2 ? .1*((i*13+j*7+variant)%19) : .1*std::abs(i-j);
    }
    const auto v=verifySolution(in,seed(),.15);
    require(v.feasible,"fixture must be independently physical");
    in.total_time_limit=*std::max_element(v.route_duration.begin(),v.route_duration.end())+
        (variant%4==0?0:(variant%4==1?.2:2));
    return in;
}
static std::vector<RoutePlan> direct(const std::vector<RoutePlan>& input,int a,int b,int t) {
    std::vector<RoutePlan> out;
    for(const auto& route:input) {
        std::map<int,int> signed_ops;
        for(const auto& op:route.operations) signed_ops[op.station]=op.pickup-op.drop;
        if(signed_ops.count(a))signed_ops[a]+=t;
        if(b && signed_ops.count(b))signed_ops[b]-=t;
        RoutePlan rebuilt{route.vehicle,{0},{}};
        for(std::size_t j=1;j+1<route.nodes.size();++j) {
            const int i=route.nodes[j],s=signed_ops.at(i);
            if(!s)continue;
            rebuilt.nodes.push_back(i);
            rebuilt.operations.push_back({i,std::max(0,s),std::max(0,-s)});
        }
        rebuilt.nodes.push_back(0);out.push_back(std::move(rebuilt));
    }
    return out;
}
struct Coverage {
    std::size_t feasible=0,load_rejected=0,time_rejected=0,stock_rejected=0;
    std::size_t sign_flips=0,deletions=0,cross_vehicle=0,adjacent_deletions=0;
};
struct Brute {bool found=false;double objective=0;std::size_t feasible=0;};
// Reference enumerates every final signed amount at a, reconstructs the full
// witness, then invokes only the original verifier. It shares no prefix-range,
// duration-delta, materializer or incremental-objective code with the module.
static Brute exhaustive(const Instance& in,const std::vector<RoutePlan>& routes,
    double lambda,Coverage& coverage) {
    const auto before=verifySolution(in,routes,lambda);require(before.feasible,"oracle input valid");
    std::map<int,int> signed_ops,owners;
    for(const auto& r:routes)for(const auto& o:r.operations) {
        signed_ops[o.station]=o.pickup-o.drop;owners[o.station]=r.vehicle;
    }
    Brute best;best.objective=before.objective;
    for(auto ia=signed_ops.begin();ia!=signed_ops.end();++ia) {
        const int a=ia->first;
        for(auto ib=ia;ib!=signed_ops.end();++ib) {
            const int b=ib==ia?0:ib->first;
            for(int value=in.initial[a]-in.capacity[a];value<=in.initial[a];++value) {
                const int t=value-ia->second;if(!t)continue;
                const auto next=direct(routes,a,b,t);
                const auto v=verifySolution(in,next,lambda);
                if(!v.feasible || !v.errors.empty()) {
                    coverage.load_rejected+=!v.load_feasible;
                    coverage.time_rejected+=!v.duration_feasible;
                    coverage.stock_rejected+=!v.station_feasible;
                    continue;
                }
                ++best.feasible;++coverage.feasible;
                coverage.cross_vehicle+=b && owners[a]!=owners[b];
                coverage.deletions+=value==0 || (b && signed_ops[b]-t==0);
                coverage.sign_flips+=(ia->second>0 && value<0)||(ia->second<0 && value>0);
                if(b && value==0 && signed_ops[b]-t==0 && owners[a]==owners[b])
                    for(const auto& route:routes)for(std::size_t j=1;j+2<route.nodes.size();++j)
                        coverage.adjacent_deletions+=
                            (route.nodes[j]==a && route.nodes[j+1]==b)||
                            (route.nodes[j]==b && route.nodes[j+1]==a);
                if(before.objective-v.objective>1e-12 && (!best.found || v.objective<best.objective)) {
                    best.found=true;best.objective=v.objective;
                }
            }
        }
    }
    return best;
}
static void compare(const Instance& in,const std::vector<RoutePlan>& routes,double lambda,Coverage& coverage) {
    Round75QuantityStats stats;
    const auto choice=bestRound75QuantityChange(in,routes,lambda,stats);
    const auto reference=exhaustive(in,routes,lambda,coverage);
    require(stats.feasible_candidates==reference.feasible,"optimized ranges/duration retain every feasible declared neighbor");
    require(choice.found==reference.found,"optimized and exhaustive improving-neighbor existence");
    if(choice.found) {
        const auto selected=applyRound75QuantityChange(routes,choice);
        const auto independent=direct(routes,choice.first,choice.second,static_cast<int>(choice.delta));
        require(canonicalCandidateSerialization(selected)==canonicalCandidateSerialization(independent),
            "production materialization agrees with independent rebuild including zero removal");
        const auto v=verifySolution(in,selected,lambda);
        require(v.feasible && v.errors.empty(),"selected neighbor fully physical");
        require(std::abs(v.objective-choice.objective)<1e-10,"coupled incremental objective matches original full formula");
        require(std::abs(v.objective-reference.objective)<1e-10,"best neighbor matches exhaustive objective optimum");
    }
}
int main() {
    try {
        Coverage coverage;int comparisons=0;std::uint64_t accepted=0,cross=0,singles=0;
        for(int variant=0;variant<24;++variant) {
            const auto in=fixture(variant);
            const double lambda=variant%3==0?0:(variant%3==1?.15:1);
            compare(in,seed(),lambda,coverage);++comparisons;
            SolveOptions options;options.lambda=lambda;
            const auto result=runRound75QuantityDescent(in,options,seed());
            require(result.verification.feasible && result.verification.errors.empty() &&
                result.stats.exhausted && !result.stats.verification_failed,"descent ends at verified exhausted neighborhood");
            require(result.verification.objective<=verifySolution(in,seed(),lambda).objective+1e-12,
                "descent retains previous original objective");
            compare(in,result.routes,lambda,coverage);++comparisons;
            Round75QuantityStats endpoint;
            require(!bestRound75QuantityChange(in,result.routes,lambda,endpoint).found,
                "no strict declared neighbor remains after exhaustion");
            const auto again=runRound75QuantityDescent(in,options,seed());
            require(canonicalCandidateSerialization(result.routes)==canonicalCandidateSerialization(again.routes),
                "quantity descent is deterministic");
            accepted+=result.stats.accepted;cross+=result.stats.cross_vehicle_moves;singles+=result.stats.single_moves;
        }
        auto zero=fixture(0);zero.initial.assign(9,0);zero.initial[3]=2;zero.initial[4]=1;
        zero.total_time_limit=100;for(auto& row:zero.dist)std::fill(row.begin(),row.end(),0);
        std::vector<RoutePlan> all_picked={{0,{0,3,4,0},{{3,2,0},{4,1,0}}}};
        const auto z=verifySolution(zero,all_picked,.15);
        require(z.feasible && z.G==0 && std::abs(z.P-1)<1e-12,"S=0 keeps original penalty convention");
        compare(zero,all_picked,.15,coverage);++comparisons;
        compare(zero,{},.15,coverage);++comparisons;
        // Explicit adjacent equal pickup/drop pair can disappear together.
        auto pair=fixture(2);pair.total_time_limit=100;
        std::vector<RoutePlan> adjacent={{0,{0,3,1,0},{{3,2,0},{1,0,2}}}};
        compare(pair,adjacent,.15,coverage);++comparisons;
        // Deadline stops the entire search, retaining its original physical input.
        SolveOptions expired;expired.process_start_time_valid=true;
        expired.process_start_time=std::chrono::steady_clock::now()-std::chrono::seconds(5);
        expired.process_wall_time_limit=1;expired.process_shutdown_margin_seconds=0;
        const auto stopped=runRound75QuantityDescent(pair,expired,adjacent);
        require(stopped.stats.deadline_reached && !stopped.stats.exhausted && !stopped.stats.accepted &&
            canonicalCandidateSerialization(stopped.routes)==canonicalCandidateSerialization(adjacent),
            "whole-run deadline preserves witness without false exhaustion");
        bool refused=false;auto invalid=adjacent;invalid[0].operations.push_back({3,2,0});
        try {runRound75QuantityDescent(pair,SolveOptions{},invalid);}catch(const std::exception&){refused=true;}
        require(refused,"duplicate operation rejected before unsafe state construction");
        refused=false;invalid=adjacent;invalid[0].operations[0].pickup=4;
        try {runRound75QuantityDescent(pair,SolveOptions{},invalid);}catch(const std::exception&){refused=true;}
        require(refused,"invalid prefix capacity rejected");
        require(coverage.feasible>1000 && coverage.load_rejected && coverage.time_rejected &&
            coverage.stock_rejected && coverage.sign_flips && coverage.deletions &&
            coverage.cross_vehicle && coverage.adjacent_deletions && accepted && cross && singles,
            "structural oracle must exercise all nontrivial declared roles");
        std::cout<<"Round75 oracle comparisons="<<comparisons<<", feasible_neighbors="<<coverage.feasible
            <<", load_rejected="<<coverage.load_rejected<<", time_rejected="<<coverage.time_rejected
            <<", stock_rejected="<<coverage.stock_rejected<<", sign_flips="<<coverage.sign_flips
            <<", deletions="<<coverage.deletions<<", cross_vehicle="<<coverage.cross_vehicle
            <<", adjacent_deletions="<<coverage.adjacent_deletions<<", accepted="<<accepted
            <<", accepted_cross_vehicle="<<cross<<", accepted_singles="<<singles<<'\n';
    } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
