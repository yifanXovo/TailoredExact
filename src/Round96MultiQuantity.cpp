#include "Round96MultiQuantity.hpp"
#include "Round95FullBlockDescent.hpp"
#include "Evaluator.hpp"
#include "ProcessPhaseLedger.hpp"
#include <algorithm>
#include <cmath>
#include <functional>
#include <limits>
#include <stdexcept>

namespace ebrp {
namespace {
using I=std::int64_t;
I floorDiv(I a,I b) { // b>0, signed mathematical floor
    const I q=a/b,r=a%b;return q-(r<0);
}
I ceilDiv(I a,I b) { return -floorDiv(-a,b); }
void restrictRay(I a,I low,I high,I& lo,I& hi) {
    if(a==0) { if(low>0||high<0)hi=lo-1;return; }
    if(a<0) {a=-a;const I save=low;low=-high;high=-save;}
    lo=std::max(lo,ceilDiv(low,a));hi=std::min(hi,floorDiv(high,a));
}
std::vector<RoutePlan> materialize(const Instance& in,const std::vector<RoutePlan>& old,
                                 const std::vector<int>& y) {
    auto out=old;
    for(auto& r:out) {
        r.operations.clear();std::vector<int> nodes{0};
        for(std::size_t j=1;j+1<r.nodes.size();++j) {
            const int i=r.nodes[j],delta=in.initial[i]-y[i];
            if(!delta)continue;
            nodes.push_back(i);r.operations.push_back({i,std::max(0,delta),std::max(0,-delta)});
        }
        nodes.push_back(0);r.nodes=std::move(nodes);
    }
    return out;
}
}

Round96MultiResult runRound96MultiQuantity(const Instance& in,const SolveOptions& opt,
                                         const std::vector<RoutePlan>& routes) {
    Round96MultiResult out;out.routes=routes;
    out.verification=verifyRound95StartingWitness(in,routes,opt.lambda);
    // Evaluator accumulates int loads and totals. Bound all potential pickups
    // and drops before enumeration; do not turn overflow into an infeasible tuple.
    for(const auto& r:routes) {
        I total=0;for(std::size_t j=1;j+1<r.nodes.size();++j)total+=in.capacity[r.nodes[j]];
        if(total>std::numeric_limits<int>::max())throw std::overflow_error("Round96 evaluator integer domain");
    }
    for(;;) {
        ++out.stats.passes;
        const auto baseline=out.verification;
        auto best_routes=out.routes;auto best=baseline;bool found=false;
        for(const auto& route:out.routes) {
            std::vector<int> stations(route.nodes.begin()+1,route.nodes.end()-1);
            std::sort(stations.begin(),stations.end());
            std::vector<int> direction(in.V+1,0),chosen;
            auto scan=[&]() {
                for(int anchor:chosen) {
                    if(processWorkDeadlineReached(opt)){out.stats.deadline=true;return;}
                    ++out.stats.directions;
                    for(int i:chosen)direction[i]=(i==anchor?int(chosen.size())-1:-1);
                    I lo=-std::numeric_limits<int>::max(),hi=std::numeric_limits<int>::max();
                    for(int i:chosen)restrictRay(direction[i],-I(baseline.final_inventory[i]),
                        I(in.capacity[i])-baseline.final_inventory[i],lo,hi);
                    I load=0,prefix=0;
                    for(std::size_t j=1;j+1<route.nodes.size();++j) {
                        const int i=route.nodes[j];load+=I(in.initial[i])-baseline.final_inventory[i];prefix+=direction[i];
                        // L'=L-prefix*t: L-Q <= prefix*t <= L.
                        restrictRay(prefix,load-in.Q[route.vehicle],load,lo,hi);
                    }
                    for(I t=lo;t<=hi;++t) {
                        if(!t)continue;
                        if(processWorkDeadlineReached(opt)){out.stats.deadline=true;return;}
                        auto y=baseline.final_inventory;
                        for(int i:chosen) {
                            I v=I(y[i])+I(direction[i])*t;
                            if(v<0||v>in.capacity[i])throw std::logic_error("Round96 ray bound incorrect");
                            y[i]=int(v);
                        }
                        ++out.stats.points;auto candidate=materialize(in,out.routes,y);
                        const auto check=verifySolution(in,candidate,opt.lambda);
                        if(!std::isfinite(check.objective))throw std::runtime_error("Round96 nonfinite objective");
                        if(!check.load_feasible||!check.station_feasible||!check.station_disjoint)
                            throw std::logic_error("Round96 exact ray domain did not preserve quantity feasibility");
                        if(!check.feasible)continue;
                        ++out.stats.physical;
                        if(check.objective<best.objective-1e-12) {
                            found=true;best=check;best_routes=std::move(candidate);
                        }
                    }
                    for(int i:chosen)direction[i]=0;
                }
            };
            for(int size:{3,4}) {
                std::function<void(std::size_t)> choose=[&](std::size_t begin) {
                    if(out.stats.deadline)return;
                    if(chosen.size()==std::size_t(size)){scan();return;}
                    for(std::size_t j=begin;j<stations.size();++j) {
                        chosen.push_back(stations[j]);choose(j+1);chosen.pop_back();
                        if(out.stats.deadline)return;
                    }
                };
                choose(0);if(out.stats.deadline)break;
            }
            if(out.stats.deadline)break;
        }
        if(out.stats.deadline)return out; // discard unfinished best, retain last accepted witness
        if(!found){out.stats.exhausted=true;return out;}
        const auto committed=verifyRound95StartingWitness(in,best_routes,opt.lambda);
        if(!(committed.objective<out.verification.objective-1e-12))throw std::logic_error("Round96 nonstrict commit");
        out.routes=std::move(best_routes);out.verification=committed;++out.stats.accepted;
        out.accepted_inventories.push_back(committed.final_inventory);
    }
}
}
