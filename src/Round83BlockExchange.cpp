#include "Round83BlockExchange.hpp"
#include "Evaluator.hpp"
#include "Round76PhysicalClosure.hpp"
#include "Round61Candidates.hpp"
#include "ProcessPhaseLedger.hpp"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <map>
#include <stdexcept>
#include <tuple>

namespace ebrp {
namespace {
using Integer = std::int64_t;
auto key(const Round83Choice& c) {
    return std::tie(c.kind,c.source,c.first,c.last,c.target,c.target_first,c.target_last);
}
struct Block { int first, last; Integer net, low, high, pickup, drop; };
struct State {
    std::vector<int> nodes;
    std::vector<Integer> load{0};
    Integer pickup = 0, drop = 0;
    std::map<Integer,std::vector<Block>> blocks;
};
void require(bool x,const char* why) { if(!x) throw std::runtime_error(why); }
double duration(const Instance& in,const std::vector<int>& nodes,Integer pickup,Integer drop) {
    if(nodes.empty())return 0;
    double travel=0;int prev=0;
    for(int i:nodes){travel+=in.dist[prev][i];prev=i;}
    travel+=in.dist[prev][0];
    const double handling=in.pickup_time*pickup+in.drop_time*drop+in.drop_time*(pickup-drop);
    return travel+handling;
}
std::vector<int> replace(const std::vector<int>& a,int first,int last,
                         const std::vector<int>& b,int bf,int bl) {
    std::vector<int> out(a.begin(),a.begin()+first);
    out.insert(out.end(),b.begin()+bf,b.begin()+bl);
    out.insert(out.end(),a.begin()+last,a.end());return out;
}
} // namespace

Round83Choice bestRound83Neutral(const Instance& in,const std::vector<RoutePlan>& routes,
    double lambda,Round83Stats& stats,const SolveOptions* deadline) {
    // Inherited enumeration also validates original instance and complete input witness.
    const auto old=bestRound78BalancedRelocation(in,routes,lambda,stats.relocation,deadline);
    Round83Choice best;
    if(old.found)best={true,0,old.source,old.first,old.last,old.target,old.leg,old.leg,old.duration_potential};
    auto expired=[&](){
        if(stats.relocation.deadline_reached || (deadline&&processWorkDeadlineReached(*deadline)))stats.deadline=true;
        return stats.deadline;
    };
    if(expired())return best;
    const auto verified=verifySolution(in,routes,lambda);
    const auto current=round78DurationPotential(verified);
    std::vector<State> state(in.M);
    std::vector<Integer> pickup(in.V+1),drop(in.V+1);
    for(const auto& r:routes) {
        auto& a=state[r.vehicle];a.nodes={r.nodes.begin()+1,r.nodes.end()-1};
        for(const auto& op:r.operations){pickup[op.station]=op.pickup;drop[op.station]=op.drop;}
        for(int i:a.nodes){a.load.push_back(a.load.back()+pickup[i]-drop[i]);a.pickup+=pickup[i];a.drop+=drop[i];}
        for(int first=0;first<static_cast<int>(a.nodes.size());++first) {
            Integer low=0,high=0,p=0,d=0;
            for(int last=first+1;last<=static_cast<int>(a.nodes.size());++last) {
                if(expired())return best;
                int i=a.nodes[last-1];p+=pickup[i];d+=drop[i];
                Integer net=a.load[last]-a.load[first];low=std::min(low,net);high=std::max(high,net);
                a.blocks[net].push_back({first,last,net,low,high,p,d});
            }
        }
    }
    for(int s=0;s<in.M;++s)for(int t=s+1;t<in.M;++t) {
        const auto& a=state[s];const auto& b=state[t];
        for(const auto& bucket:a.blocks) {
            auto match=b.blocks.find(bucket.first);if(match==b.blocks.end())continue;
            for(const auto& x:bucket.second)for(const auto& y:match->second) {
                if(expired())return best;
                ++stats.equal_net_pairs;
                if(a.load[x.first]+y.low<0 || a.load[x.first]+y.high>in.Q[s] ||
                   b.load[y.first]+x.low<0 || b.load[y.first]+x.high>in.Q[t])continue;
                ++stats.load_feasible;
                const auto an=replace(a.nodes,x.first,x.last,b.nodes,y.first,y.last);
                const auto bn=replace(b.nodes,y.first,y.last,a.nodes,x.first,x.last);
                const double da=duration(in,an,a.pickup-x.pickup+y.pickup,a.drop-x.drop+y.drop);
                const double db=duration(in,bn,b.pickup-y.pickup+x.pickup,b.drop-y.drop+x.drop);
                if(!std::isfinite(da)||!std::isfinite(db)||da>in.total_time_limit+1e-7||db>in.total_time_limit+1e-7)continue;
                ++stats.feasible;
                auto potential=verified.route_duration;potential[s]=da;potential[t]=db;
                std::sort(potential.begin(),potential.end(),std::greater<double>());
                if(!(potential<current))continue;
                ++stats.improving;
                Round83Choice c{true,1,s,x.first,x.last,t,y.first,y.last,potential};
                if(!best.found||potential<best.duration_potential||
                    (potential==best.duration_potential&&key(c)<key(best)))best=std::move(c);
            }
        }
    }
    return best;
}

std::vector<RoutePlan> applyRound83Neutral(const std::vector<RoutePlan>& routes,const Round83Choice& c) {
    if(c.kind==0) {
        if(c.target_first!=c.target_last)throw std::invalid_argument("Relocation target must be an empty interval");
        return applyRound78BalancedRelocation(routes,{c.found,c.source,c.first,c.last,c.target,c.target_first,c.duration_potential});
    }
    if(!c.found||c.kind!=1||c.source<0||c.source>=c.target||c.first<0||c.last<=c.first||
        c.target_first<0||c.target_last<=c.target_first)throw std::invalid_argument("Invalid equal-net exchange choice");
    auto out=routes;
    auto a=std::find_if(out.begin(),out.end(),[&](const auto& r){return r.vehicle==c.source;});
    auto b=std::find_if(out.begin(),out.end(),[&](const auto& r){return r.vehicle==c.target;});
    if(a==out.end()||b==out.end()||c.last>static_cast<int>(a->nodes.size())-2||
       c.target_last>static_cast<int>(b->nodes.size())-2)throw std::invalid_argument("Exchange interval outside route");
    std::map<int,StopOperation> ops;
    for(const auto& r:routes)for(const auto& op:r.operations)ops.emplace(op.station,op);
    std::vector<int> an(a->nodes.begin()+1,a->nodes.end()-1),bn(b->nodes.begin()+1,b->nodes.end()-1);
    Integer na=0,nb=0;
    for(int j=c.first;j<c.last;++j){const auto& op=ops.at(an[j]);na+=Integer(op.pickup)-op.drop;}
    for(int j=c.target_first;j<c.target_last;++j){const auto& op=ops.at(bn[j]);nb+=Integer(op.pickup)-op.drop;}
    if(na!=nb)throw std::invalid_argument("Exchange blocks have different net loads");
    auto set=[&](RoutePlan& r,const std::vector<int>& sequence){
        r.nodes={0};r.operations.clear();
        for(int i:sequence){r.nodes.push_back(i);r.operations.push_back(ops.at(i));}r.nodes.push_back(0);
    };
    set(*a,replace(an,c.first,c.last,bn,c.target_first,c.target_last));
    set(*b,replace(bn,c.target_first,c.target_last,an,c.first,c.last));
    std::sort(out.begin(),out.end(),[](const auto& a,const auto& b){return a.vehicle<b.vehicle;});return out;
}

Round83Result runRound83ExchangeDescent(const Instance& in,const SolveOptions& opt,
    const std::vector<RoutePlan>& routes,const std::filesystem::path& out) {
    Round83Result result;result.routes=routes;result.verification=verifySolution(in,routes,opt.lambda);
    require(result.verification.feasible&&result.verification.errors.empty()&&
        result.verification.original_objective_recomputed,"Invalid exchange descent input");
    if(!out.empty()) {
        std::filesystem::create_directories(out);
        require(!std::filesystem::exists(out/"initial.json"),"Exchange trace directory already used");
        std::ofstream matrix(out/"actual_distances.json");matrix<<std::setprecision(17)<<'[';
        for(int i=0;i<=in.V;++i){if(i)matrix<<',';matrix<<'[';
            for(int j=0;j<=in.V;++j){if(j)matrix<<',';matrix<<in.dist[i][j];}matrix<<']';}
        matrix<<"]\n";matrix.close();require(bool(matrix),"Distance snapshot failed");
    }
    auto snapshot=[&](const std::filesystem::path& path){
        if(out.empty())return;
        VerifiedCandidateStore store;
        require(store.consider(in,opt.lambda,result.routes,"round83_exchange_descent","original_problem"),"Exchange snapshot failed");
        writeRound61Witness(path,in,opt.lambda,store.best());
    };
    snapshot(out/"initial.json");
    std::ofstream events;if(!out.empty()){events.open(out/"events.jsonl");require(bool(events),"Cannot open exchange events");events<<std::setprecision(17);}
    for(std::uint64_t iteration=0;;++iteration) {
        if(result.verification.objective==0){result.zero=true;break;}
        if(processWorkDeadlineReached(opt)){result.deadline=true;break;}
        auto strict=runRound76PhysicalClosure(in,opt,result.routes,out.empty()?std::filesystem::path{}:out/("closure_"+std::to_string(iteration)+".csv"));
        if(strict.stats.verification_failed){result.verification_failed=true;break;}
        result.routes=std::move(strict.routes);result.verification=std::move(strict.verification);
        result.insertions+=strict.stats.accepted_insertions;result.quantities+=strict.stats.accepted_quantities;
        result.insertion_evaluations+=strict.stats.insertion.quantity_evaluations;
        result.quantity_evaluations+=strict.stats.quantity.objective_evaluations;
        if(strict.stats.deadline_reached){result.deadline=true;break;}
        require(strict.stats.exhausted,"Strict closure unexplained stop");
        if(result.verification.objective==0){result.zero=true;break;}
        Round83Stats stats;auto move=bestRound83Neutral(in,result.routes,opt.lambda,stats,&opt);
        result.equal_net_pairs+=stats.equal_net_pairs;result.block_placements+=stats.relocation.placements;
        if(stats.deadline){result.deadline=true;break;}
        if(events.is_open()) {
            events<<"{\"iteration\":"<<iteration<<",\"kind\":"<<move.kind<<",\"source\":"<<move.source
              <<",\"first\":"<<move.first<<",\"last\":"<<move.last<<",\"target\":"<<move.target
              <<",\"target_first\":"<<move.target_first<<",\"target_last\":"<<move.target_last
              <<",\"balanced_blocks\":"<<stats.relocation.balanced_blocks<<",\"placements\":"<<stats.relocation.placements
              <<",\"feasible\":"<<stats.relocation.feasible_placements<<",\"improving\":"<<stats.relocation.improving_placements
              <<",\"exchange_pairs\":"<<stats.equal_net_pairs<<",\"exchange_load_feasible\":"<<stats.load_feasible
              <<",\"exchange_feasible\":"<<stats.feasible<<",\"exchange_improving\":"<<stats.improving
              <<",\"F\":"<<result.verification.objective<<",\"found\":"<<(move.found?"true":"false")<<"}\n";
            events.flush();require(bool(events),"Exchange event write failed");
        }
        if(!move.found){result.exhausted=true;break;}
        auto next=applyRound83Neutral(result.routes,move);auto checked=verifySolution(in,next,opt.lambda);
        if(!checked.feasible||!checked.errors.empty()||!checked.original_objective_recomputed||
            checked.final_inventory!=result.verification.final_inventory||checked.objective!=result.verification.objective||
            round78DurationPotential(checked)!=move.duration_potential||
            !(move.duration_potential<round78DurationPotential(result.verification))) {result.verification_failed=true;break;}
        result.routes=std::move(next);result.verification=std::move(checked);++result.neutral;
        if(move.kind==0)++result.relocations;else ++result.exchanges;
        snapshot(out/("neutral_"+std::to_string(iteration)+".json"));
    }
    snapshot(out/"final.json");
    if(!out.empty()) {
        std::ofstream summary(out/"result.json");summary<<std::setprecision(17)
            <<"{\"F\":"<<result.verification.objective<<",\"neutral\":"<<result.neutral
            <<",\"relocations\":"<<result.relocations<<",\"exchanges\":"<<result.exchanges
            <<",\"equal_net_pairs\":"<<result.equal_net_pairs<<",\"insertions\":"<<result.insertions
            <<",\"quantities\":"<<result.quantities<<",\"exhausted\":"<<(result.exhausted?"true":"false")
            <<",\"deadline\":"<<(result.deadline?"true":"false")<<",\"zero\":"<<(result.zero?"true":"false")
            <<",\"verification_failed\":"<<(result.verification_failed?"true":"false")<<",\"optimizer_calls\":0}\n";
        summary.flush();require(bool(summary),"Exchange result write failed");
    }
    return result;
}
} // namespace ebrp
