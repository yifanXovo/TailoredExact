#include "Round73JointInsertion.hpp"
#include "Evaluator.hpp"
#include "Round60Candidates.hpp"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <iostream>
#include <set>
#include <stdexcept>

using namespace ebrp;
static void require(bool condition,const char* reason) {
    if(!condition)throw std::runtime_error(reason);
}
static Instance fixture(int variant) {
    Instance in;in.V=8;in.M=2;in.Q={2,3};
    in.initial={0,4,0,4,0,4,0,3,1};in.capacity.assign(9,5);
    in.target={0,2,3,2,1,2,3,1,2};in.weights={0,.10,.15,.20,.05,.10,.15,.10,.15};
    in.total_time_limit=variant%3==0?19:40;
    in.pickup_time=variant%2?.3:0;in.drop_time=variant%2?.7:0;
    in.dist.assign(9,std::vector<double>(9));
    for(int i=0;i<=8;++i)for(int j=0;j<=8;++j) {
        const double xi=(i*7+variant)%11,yi=(i*3+variant)%7;
        const double xj=(j*7+variant)%11,yj=(j*3+variant)%7;
        in.dist[i][j]=std::hypot(xi-xj,yi-yj)*.35;
    }
    return in;
}

// Reference deliberately materializes and physically verifies every quantity
// at every placement. It does not use the optimized qmax/range/load reduction
// or incremental objective. No MIP or historical solution enters this oracle.
static std::vector<RoutePlan> directInsert(std::vector<RoutePlan> routes,int vehicle,
    int pick,int drop,int q,int a,int b) {
    auto it=std::find_if(routes.begin(),routes.end(),[&](const RoutePlan& r){return r.vehicle==vehicle;});
    if(it==routes.end()){routes.push_back({vehicle,{0,0},{}});it=routes.end()-1;}
    if(drop) {it->nodes.insert(it->nodes.begin()+b+1,drop);it->operations.push_back({drop,0,q});}
    if(pick) {it->nodes.insert(it->nodes.begin()+a+1,pick);it->operations.push_back({pick,q,0});}
    return routes;
}
struct Brute {bool found=false,free=false;double score=0,gain=0;std::size_t feasible=0;};
static Brute exhaustive(const Instance& in,const std::vector<RoutePlan>& routes,double lambda) {
    const auto start=verifySolution(in,routes,lambda);require(start.feasible,"reference seed feasible");
    std::set<int> visited;for(const auto& r:routes)for(int i:r.nodes)visited.insert(i);
    Brute best;
    for(int pick=0;pick<=in.V;++pick)for(int drop=0;drop<=in.V;++drop) {
        if((!pick&&!drop)||pick==drop||(pick&&visited.count(pick))||(drop&&visited.count(drop)))continue;
        for(int k=0;k<in.M;++k) {
            const auto it=std::find_if(routes.begin(),routes.end(),[&](const RoutePlan& r){return r.vehicle==k;});
            const int legs=it==routes.end()?1:static_cast<int>(it->nodes.size())-1;
            for(int a=0;a<legs;++a)for(int b=pick&&drop?a:0;b<legs;++b) {
                if(!(pick&&drop) && b!=0)continue;
                const int pa=pick?a:-1,db=drop?(pick?b:a):-1;
                for(int q=1;q<=in.Q[k];++q) {
                    const auto candidate=directInsert(routes,k,pick,drop,q,pa,db);
                    const auto checked=verifySolution(in,candidate,lambda);
                    if(!checked.feasible||!checked.errors.empty())continue;
                    ++best.feasible;
                    const double gain=start.objective-checked.objective;
                    if(!(gain>1e-12))continue;
                    const double added=checked.route_duration[k]-start.route_duration[k];
                    const bool free=added<=0;
                    const double score=free?gain:gain/added;
                    if(!best.found || (free&&!best.free) || (free==best.free && score>best.score)) {
                        best.found=true;best.free=free;best.score=score;best.gain=gain;
                    }
                }
            }
        }
    }
    return best;
}
static std::size_t compare(const Instance& in,const std::vector<RoutePlan>& routes,double lambda) {
    Round73InsertionStats stats;
    const auto optimized=bestRound73Insertion(in,routes,lambda,stats);
    const auto brute=exhaustive(in,routes,lambda);
    require(optimized.found==brute.found,"reduced search finds exactly the existence of improving motifs");
    if(optimized.found) {
        const auto physical=verifySolution(in,applyRound73Insertion(routes,optimized),lambda);
        require(physical.feasible&&physical.errors.empty(),"selected reduced motif physically feasible");
        require(std::fabs(physical.objective-optimized.objective)<1e-10,"incremental original objective matches full recomputation");
        const auto prior=verifySolution(in,routes,lambda);
        const double added=physical.route_duration[optimized.vehicle]-prior.route_duration[optimized.vehicle];
        require(std::fabs(added-optimized.added_duration)<1e-10,"handling includes depot unloading exactly once");
        const bool free=optimized.added_duration<=0;
        const double score=free?optimized.gain:optimized.gain/optimized.added_duration;
        require(free==brute.free&&std::fabs(score-brute.score)<1e-9*std::max(1.0,std::fabs(score)),
            "minimum-placement reduction preserves the exhaustive best physical-duration score");
    }
    return brute.feasible;
}
int main() {
    try {
        std::size_t enumerated=0;int comparisons=0;
        for(int variant=0;variant<12;++variant) {
            auto in=fixture(variant);
            const double lambda=variant%3==0?0:(variant%3==1?.15:1);
            enumerated+=compare(in,{},lambda);++comparisons;
            std::vector<RoutePlan> seed={{0,{0,1,2,3,4,0},{{1,2,0},{2,0,2},{3,2,0},{4,0,1}}}};
            const auto physical=verifySolution(in,seed,lambda);
            require(physical.feasible,"prefix fixture includes cumulative pickups4 > capacity2 and loaded return1");
            enumerated+=compare(in,seed,lambda);++comparisons;
            SolveOptions opt;opt.lambda=lambda;
            const auto built=runRound73JointInsertion(in,opt);
            require(built.verification.feasible&&built.verification.errors.empty()&&built.stats.exhausted,
                "production constructor has a verified motif-exhausted endpoint");
            require(built.stats.accepted<=in.V,"finite station-addition invariant");
            const auto again=runRound73JointInsertion(in,opt);
            require(canonicalCandidateSerialization(built.routes)==canonicalCandidateSerialization(again.routes),
                "constructor is deterministic without a seed contest");
            enumerated+=compare(in,built.routes,lambda);++comparisons;
        }
        auto zero=fixture(0);zero.initial.assign(9,0);
        SolveOptions opt;const auto empty=runRound73JointInsertion(zero,opt);
        require(empty.stats.exhausted&&empty.stats.accepted==0&&empty.verification.G==0&&
            std::fabs(empty.verification.objective-.15)<1e-12,"S=0 uses the original nonzero penalty convention");
        auto free=fixture(1);free.pickup_time=free.drop_time=0;
        for(auto& row:free.dist)std::fill(row.begin(),row.end(),0);
        enumerated+=compare(free,{},.15);++comparisons;
        require(runRound73JointInsertion(free,opt).stats.exhausted,"zero-duration priority terminates without division by zero");
        opt.process_start_time_valid=true;opt.process_start_time=std::chrono::steady_clock::now()-std::chrono::seconds(5);
        opt.process_wall_time_limit=1;opt.process_shutdown_margin_seconds=0;
        const auto expired=runRound73JointInsertion(free,opt);
        require(expired.stats.deadline_reached&&!expired.stats.exhausted&&expired.stats.accepted==0,
            "whole-run deadline is not reported as mathematical exhaustion");
        bool refused=false;auto bad=fixture(0);bad.initial[1]=100;
        try{runRound73JointInsertion(bad,SolveOptions{});}catch(const std::exception&){refused=true;}
        require(refused,"invalid no-service start is rejected without inventing an incumbent");
        require(enumerated>1000,"exhaustive comparison must exercise substantive feasible placements");
        std::cout<<"Round73 structural checks: comparisons="<<comparisons<<", independently feasible motifs="<<enumerated<<"\n";
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
