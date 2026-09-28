#include "Round96RouteOrder.hpp"
#include "Round95FullBlockDescent.hpp"
#include "Evaluator.hpp"
#include "ProcessPhaseLedger.hpp"
#include "Round61Candidates.hpp"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <stdexcept>

namespace ebrp {
namespace {
std::vector<RoutePlan> completeRoutes(const Instance& in,const std::vector<RoutePlan>& routes) {
    auto result=routes;std::vector<bool> seen(in.M,false);
    for(const auto& r:result) {
        if(r.vehicle<0||r.vehicle>=in.M||seen[r.vehicle])throw std::invalid_argument("Invalid order vehicle");
        seen[r.vehicle]=true;
    }
    for(int k=0;k<in.M;++k)if(!seen[k])result.push_back(RoutePlan{k,{0,0},{}});
    std::sort(result.begin(),result.end(),[](const RoutePlan& a,const RoutePlan& b){return a.vehicle<b.vehicle;});
    return result;
}
}
Round96OrderResult runRound96RouteOrder(const Instance& in,const SolveOptions& opt,
    const std::vector<RoutePlan>& routes,const std::filesystem::path& trace) {
    if(in.M<1)throw std::invalid_argument("Invalid order fleet");
    Round96OrderResult out;out.routes=completeRoutes(in,routes);
    out.verification=verifyRound95StartingWitness(in,out.routes,opt.lambda);
    std::ofstream events;
    if(!trace.empty()) {
        if(std::filesystem::exists(trace))throw std::invalid_argument("Route-order trace exists");
        std::filesystem::create_directories(trace);events.open(trace/"events.jsonl");
        if(!events)throw std::runtime_error("Route-order trace open failed");
        events<<std::setprecision(17);
    }
    auto snapshot=[&](const std::string& name) {
        if(trace.empty())return;
        VerifiedCandidateStore store;
        if(!store.consider(in,opt.lambda,out.routes,"round96_route_order","original_problem"))
            throw std::runtime_error("Route-order snapshot verification failed");
        writeRound61Witness(trace/name,in,opt.lambda,store.best());
    };
    snapshot("initial.json");
    for(;;) {
        if(processWorkDeadlineReached(opt)){out.stats.deadline=true;break;}
        auto old=runRound83ExchangeDescent(in,opt,out.routes,
            trace.empty()?std::filesystem::path{}:trace/("old_"+std::to_string(out.stats.passes)));
        out.stats.old_neutral+=old.neutral;out.stats.insertions+=old.insertions;out.stats.quantities+=old.quantities;
        out.routes=completeRoutes(in,old.routes);
        out.verification=verifyRound95StartingWitness(in,out.routes,opt.lambda);
        if(old.verification_failed){out.stats.verification_failed=true;break;}
        if(old.deadline){out.stats.deadline=true;break;}
        if(old.zero){out.stats.zero=true;break;}
        if(!old.exhausted)throw std::runtime_error("Unexplained old closure stop");
        ++out.stats.passes;
        const auto current=round78DurationPotential(out.verification);
        auto best=current;auto best_routes=out.routes;bool found=false;
        for(std::size_t ri=0;ri<out.routes.size();++ri) {
            const auto& route=out.routes[ri];const int size=static_cast<int>(route.nodes.size())-2;
            std::vector<int> nodes(route.nodes.begin()+1,route.nodes.end()-1);
            std::vector<std::int64_t> delta(in.V+1,0);
            std::int64_t pickup=0,drop=0;
            for(const auto& op:route.operations) {
                delta[op.station]=std::int64_t(op.pickup)-op.drop;pickup+=op.pickup;drop+=op.drop;
            }
            const double handling=in.pickup_time*pickup+in.drop_time*drop+in.drop_time*(pickup-drop);
            for(int a=0;a<size&&!out.stats.deadline;++a)
            for(int b=a+1;b<size&&!out.stats.deadline;++b)
            for(int c=b+1;c<=size&&!out.stats.deadline;++c)
            for(int swap=0;swap<2&&!out.stats.deadline;++swap)
            for(int ra=0;ra<2&&!out.stats.deadline;++ra)
            for(int rb=0;rb<2&&!out.stats.deadline;++rb) {
                if(!swap&&!ra&&!rb)continue;
                if(processWorkDeadlineReached(opt)){out.stats.deadline=true;break;}
                ++out.stats.proposals;
                std::vector<int> first(nodes.begin()+a,nodes.begin()+b),second(nodes.begin()+b,nodes.begin()+c);
                if(ra)std::reverse(first.begin(),first.end());
                if(rb)std::reverse(second.begin(),second.end());
                if(swap)std::swap(first,second);
                std::vector<int> next(nodes.begin(),nodes.begin()+a);
                next.insert(next.end(),first.begin(),first.end());next.insert(next.end(),second.begin(),second.end());
                next.insert(next.end(),nodes.begin()+c,nodes.end());
                if(next==nodes)continue;
                std::int64_t load=0;bool feasible=true;
                for(int i:next){load+=delta[i];if(load<0||load>in.Q[route.vehicle]){feasible=false;break;}}
                if(!feasible)continue;
                ++out.stats.load_feasible;
                double travel=0;int previous=0;
                for(int i:next){travel+=in.dist[previous][i];previous=i;}travel+=in.dist[previous][0];
                const double duration=travel+handling;
                if(!std::isfinite(duration)||duration>in.total_time_limit+1e-7)continue;
                ++out.stats.duration_feasible;
                auto potential=out.verification.route_duration;potential[route.vehicle]=duration;
                std::sort(potential.begin(),potential.end(),std::greater<double>());
                if(!(potential<best))continue;
                best_routes=out.routes;auto& changed=best_routes[ri];changed.nodes={0};
                changed.nodes.insert(changed.nodes.end(),next.begin(),next.end());changed.nodes.push_back(0);
                best=std::move(potential);found=true;
            }
            if(out.stats.deadline)break;
        }
        if(out.stats.deadline)break; // never commit a partly enumerated best
        if(!found){out.stats.exhausted=true;break;}
        auto checked=verifySolution(in,best_routes,opt.lambda);
        if(!checked.feasible||!checked.errors.empty()||!checked.original_objective_recomputed||
            checked.final_inventory!=out.verification.final_inventory||checked.objective!=out.verification.objective||
            round78DurationPotential(checked)!=best||!(best<current)) {
            out.stats.verification_failed=true;break;
        }
        out.routes=std::move(best_routes);out.verification=std::move(checked);++out.stats.accepted;
        snapshot("order_"+std::to_string(out.stats.accepted)+".json");
        if(events.is_open()) {
            events<<"{\"accepted\":"<<out.stats.accepted<<",\"F\":"<<out.verification.objective<<",\"duration\":[";
            for(std::size_t i=0;i<best.size();++i){if(i)events<<',';events<<best[i];}events<<"]}\n";
            events.flush();if(!events)throw std::runtime_error("Route-order trace write failed");
        }
    }
    snapshot("final.json");return out;
}
} // namespace ebrp
