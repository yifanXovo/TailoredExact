#include "Round73JointInsertion.hpp"
#include "Evaluator.hpp"
#include "ProcessPhaseLedger.hpp"

#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <limits>
#include <stdexcept>
#include <tuple>

namespace ebrp {
namespace {
constexpr double improvement = 1e-12;
constexpr double physical_tolerance = 1e-7; // same duration test as Evaluator

bool expired(const SolveOptions* options, Round73InsertionStats& stats) {
    if (options && processWorkDeadlineReached(*options)) stats.deadline_reached = true;
    return stats.deadline_reached;
}

void requireInput(const Instance& in, const std::vector<RoutePlan>& routes) {
    if (in.V < 1 || in.M < 1 || in.Q.size() != static_cast<std::size_t>(in.M) ||
        in.initial.size() != static_cast<std::size_t>(in.V+1) ||
        in.capacity.size() != in.initial.size() || in.target.size() != in.initial.size() ||
        in.weights.size() != in.initial.size() || in.dist.size() != in.initial.size() ||
        !std::isfinite(in.pickup_time) || !std::isfinite(in.drop_time) ||
        in.pickup_time < 0 || in.drop_time < 0 || !std::isfinite(in.total_time_limit))
        throw std::runtime_error("Joint insertion requires a valid original instance");
    for (int i=0; i<=in.V; ++i) {
        if (in.dist[i].size()!=in.initial.size() || (i && in.target[i]<=0))
            throw std::runtime_error("Joint insertion instance dimension/target mismatch");
        for (double d:in.dist[i]) if (!std::isfinite(d) || d<0)
            throw std::runtime_error("Joint insertion requires finite nonnegative travel");
    }
    for (int q:in.Q) if(q<0) throw std::runtime_error("Negative vehicle capacity");
    std::vector<bool> vehicle(in.M,false);
    for (const auto& route:routes) {
        if(route.vehicle<0 || route.vehicle>=in.M || vehicle[route.vehicle])
            throw std::runtime_error("Joint insertion requires one route per vehicle");
        vehicle[route.vehicle]=true;
        if(route.nodes.size()<2 || route.nodes.front()!=0 || route.nodes.back()!=0)
            throw std::runtime_error("Joint insertion route endpoint mismatch");
        for(std::size_t j=1;j+1<route.nodes.size();++j)
            if(route.nodes[j]<=0 || route.nodes[j]>in.V)
                throw std::runtime_error("Joint insertion route station mismatch");
    }
}

struct ObjectiveDelta {
    const Instance& in;
    const std::vector<int>& inventory;
    double lambda;
    std::vector<long double> ratios;
    long double S=0,H=0,P=0;
    ObjectiveDelta(const Instance& instance,const std::vector<int>& y,double weight)
        :in(instance),inventory(y),lambda(weight),ratios(in.V+1) {
        for(int i=1;i<=in.V;++i) {
            ratios[i]=static_cast<long double>(y[i])/in.target[i];
            S+=ratios[i]; P+=in.weights[i]*std::fabs(ratios[i]-1);
            for(int j=1;j<i;++j) H+=std::fabs(ratios[i]-ratios[j]);
        }
    }
    double changed(int pick,int drop,int q) const {
        const long double rp=pick?ratios[pick]-static_cast<long double>(q)/in.target[pick]:0;
        const long double rd=drop?ratios[drop]+static_cast<long double>(q)/in.target[drop]:0;
        long double s=S,h=H,p=P;
        if(pick) {s+=rp-ratios[pick];p+=in.weights[pick]*(std::fabs(rp-1)-std::fabs(ratios[pick]-1));}
        if(drop) {s+=rd-ratios[drop];p+=in.weights[drop]*(std::fabs(rd-1)-std::fabs(ratios[drop]-1));}
        for(int i=1;i<=in.V;++i) if(i!=pick && i!=drop) {
            if(pick) h+=std::fabs(rp-ratios[i])-std::fabs(ratios[pick]-ratios[i]);
            if(drop) h+=std::fabs(rd-ratios[i])-std::fabs(ratios[drop]-ratios[i]);
        }
        if(pick && drop) h+=std::fabs(rp-rd)-std::fabs(ratios[pick]-ratios[drop]);
        // Near cancellation, use the original full formula; never invent a
        // different S=0 convention or numerically negative Gini value.
        if(s<1e-12L || h<1e-12L) {
            auto y=inventory; if(pick)y[pick]-=q;if(drop)y[drop]+=q;
            return computeObjectiveParts(in,y,lambda).objective;
        }
        return static_cast<double>(h/(in.V*s)+lambda*p);
    }
};

bool better(const Round73InsertionChoice& a,const Round73InsertionChoice& b) {
    if(!b.found)return true;
    const bool free_a=a.added_duration<=0,free_b=b.added_duration<=0;
    if(free_a!=free_b)return free_a;
    const long double left=free_a?a.gain:static_cast<long double>(a.gain)*b.added_duration;
    const long double right=free_b?b.gain:static_cast<long double>(b.gain)*a.added_duration;
    if(left!=right)return left>right;
    if(a.gain!=b.gain)return a.gain>b.gain;
    if(a.added_duration!=b.added_duration)return a.added_duration<b.added_duration;
    return std::tie(a.pickup,a.drop,a.quantity,a.vehicle,a.pickup_leg,a.drop_leg)<
           std::tie(b.pickup,b.drop,b.quantity,b.vehicle,b.pickup_leg,b.drop_leg);
}

struct Placement { bool found=false;int vehicle=-1,a=-1,b=-1;double delta=0; };
bool betterPlacement(const Placement& a,const Placement& b) {
    return !b.found || a.delta<b.delta ||
        (a.delta==b.delta && std::tie(a.vehicle,a.a,a.b)<std::tie(b.vehicle,b.a,b.b));
}
struct RouteState {
    RoutePlan route;
    std::vector<int> load;
    std::vector<std::vector<int>> maximum;
    std::vector<int> suffix_minimum;
    double duration=0;
};
} // namespace

Round73InsertionChoice bestRound73Insertion(const Instance& in,
    const std::vector<RoutePlan>& routes,double lambda,Round73InsertionStats& stats,
    const SolveOptions* deadline) {
    requireInput(in,routes);
    const auto verified=verifySolution(in,routes,lambda);
    if(!verified.feasible || !verified.errors.empty())
        throw std::runtime_error("Joint insertion refuses an invalid physical prefix");
    ++stats.passes;
    Round73InsertionChoice best;
    if(expired(deadline,stats))return best;
    std::vector<bool> visited(in.V+1,false);
    std::vector<RouteState> states(in.M);
    for(int k=0;k<in.M;++k)states[k].route={k,{0,0},{}};
    for(const auto& route:routes)states[route.vehicle].route=route;
    for(auto& state:states) {
        const auto& route=state.route;
        state.duration=verified.route_duration[route.vehicle];
        const int legs=static_cast<int>(route.nodes.size())-1;
        state.load.assign(legs,0);
        for(int a=1;a<legs;++a) {
            const int i=route.nodes[a];visited[i]=true;
            auto op=std::find_if(route.operations.begin(),route.operations.end(),
                [i](const StopOperation& x){return x.station==i;});
            state.load[a]=state.load[a-1]+op->pickup-op->drop;
        }
        state.maximum.assign(legs,std::vector<int>(legs));
        state.suffix_minimum=state.load;
        for(int a=0;a<legs;++a)for(int b=a;b<legs;++b)
            state.maximum[a][b]=b==a?state.load[b]:std::max(state.maximum[a][b-1],state.load[b]);
        for(int a=legs-2;a>=0;--a)state.suffix_minimum[a]=std::min(state.load[a],state.suffix_minimum[a+1]);
    }
    const ObjectiveDelta objective(in,verified.final_inventory,lambda);
    const double handling=in.pickup_time+in.drop_time;
    const int largest_q=*std::max_element(in.Q.begin(),in.Q.end());
    // Zero denotes the absence of that side, yielding single pickup/drop.
    for(int pick=0;pick<=in.V;++pick) for(int drop=0;drop<=in.V;++drop) {
        if((!pick && !drop) || pick==drop || (pick && visited[pick]) || (drop && visited[drop]))continue;
        if(expired(deadline,stats))return best;
        int limit=largest_q;
        if(pick)limit=std::min(limit,verified.final_inventory[pick]);
        if(drop)limit=std::min(limit,in.capacity[drop]-verified.final_inventory[drop]);
        if(limit<1)continue;
        std::vector<Placement> by_maximum(static_cast<std::size_t>(limit)+1);
        for(const auto& state:states) {
            const auto& r=state.route;
            const int legs=static_cast<int>(state.load.size());
            auto considerPlacement=[&](int a,int b,double delta,int capacity) {
                ++stats.placements;
                int qmax=std::min(limit,capacity);
                const double remaining=in.total_time_limit+physical_tolerance-state.duration-delta;
                if(qmax<1 || remaining<0)return;
                if(pick && handling>0) {
                    const double possible=std::floor(remaining/handling);
                    if(possible<qmax)qmax=static_cast<int>(std::max(0.0,possible));
                }
                if(qmax<1)return;
                Placement p{true,r.vehicle,a,b,delta};
                if(betterPlacement(p,by_maximum[qmax]))by_maximum[qmax]=p;
            };
            for(int a=0;a<legs;++a) {
                if(expired(deadline,stats))return best;
                const int before=r.nodes[a],after=r.nodes[a+1];
                if(pick && drop)for(int b=a;b<legs;++b) {
                    double delta;
                    if(a==b)delta=in.dist[before][pick]+in.dist[pick][drop]+in.dist[drop][after]-in.dist[before][after];
                    else delta=in.dist[before][pick]+in.dist[pick][after]-in.dist[before][after]+
                        in.dist[r.nodes[b]][drop]+in.dist[drop][r.nodes[b+1]]-in.dist[r.nodes[b]][r.nodes[b+1]];
                    considerPlacement(a,b,delta,in.Q[r.vehicle]-state.maximum[a][b]);
                } else {
                    const int station=pick?pick:drop;
                    const double delta=in.dist[before][station]+in.dist[station][after]-in.dist[before][after];
                    considerPlacement(pick?a:-1,drop?a:-1,delta,
                        pick?in.Q[r.vehicle]-state.maximum[a][legs-1]:state.suffix_minimum[a]);
                }
            }
        }
        Placement cheapest;
        for(int q=limit;q>=1;--q) {
            if(by_maximum[q].found && betterPlacement(by_maximum[q],cheapest))cheapest=by_maximum[q];
            if(!cheapest.found)continue;
            if(expired(deadline,stats))return best;
            ++stats.quantity_evaluations;
            const double value=objective.changed(pick,drop,q);
            const double gain=verified.objective-value;
            if(!std::isfinite(value) || !(gain>improvement))continue;
            Round73InsertionChoice candidate{true,cheapest.vehicle,pick,drop,q,
                cheapest.a,cheapest.b,cheapest.delta,
                cheapest.delta+(pick?handling*q:0),value,gain};
            if(better(candidate,best))best=candidate;
        }
    }
    return best;
}

std::vector<RoutePlan> applyRound73Insertion(const std::vector<RoutePlan>& routes,
                                          const Round73InsertionChoice& c) {
    if(!c.found || c.quantity<=0 || (!c.pickup && !c.drop))
        throw std::runtime_error("Cannot apply an empty joint insertion");
    auto out=routes;
    auto it=std::find_if(out.begin(),out.end(),[&](const RoutePlan& r){return r.vehicle==c.vehicle;});
    if(it==out.end()) {out.push_back({c.vehicle,{0,0},{}});it=out.end()-1;}
    RoutePlan next{c.vehicle,{it->nodes.front()},it->operations};
    if(c.pickup)next.operations.push_back({c.pickup,c.quantity,0});
    if(c.drop)next.operations.push_back({c.drop,0,c.quantity});
    for(int leg=0;leg+1<static_cast<int>(it->nodes.size());++leg) {
        if(c.pickup && leg==c.pickup_leg)next.nodes.push_back(c.pickup);
        if(c.drop && leg==c.drop_leg)next.nodes.push_back(c.drop);
        next.nodes.push_back(it->nodes[leg+1]);
    }
    *it=std::move(next);
    std::sort(out.begin(),out.end(),[](const RoutePlan& a,const RoutePlan& b){return a.vehicle<b.vehicle;});
    return out;
}

Round73InsertionResult runRound73JointInsertion(const Instance& in,const SolveOptions& options,
                                               const std::filesystem::path& trace_path) {
    Round73InsertionResult out;
    requireInput(in,out.routes);
    out.verification=verifySolution(in,out.routes,options.lambda);
    if(!out.verification.feasible || !out.verification.errors.empty())
        throw std::runtime_error("Joint insertion no-service start is not physically legal");
    std::ofstream trace;
    if(!trace_path.empty()) {
        if(trace_path.has_parent_path())std::filesystem::create_directories(trace_path.parent_path());
        trace.open(trace_path);
        if(!trace)throw std::runtime_error("Cannot open joint insertion evidence");
        trace<<"step,process_seconds,vehicle,pickup,drop,quantity,pickup_leg,drop_leg,travel_delta,added_duration,objective,G,P,placements,quantity_evaluations,status\n"<<std::setprecision(17);
    }
    auto write=[&](const Round73InsertionChoice& c,const char* status) {
        if(!trace.is_open())return;
        trace<<out.stats.accepted<<','<<processElapsedSeconds(options)<<','<<c.vehicle<<','<<c.pickup<<','<<c.drop<<','
            <<c.quantity<<','<<c.pickup_leg<<','<<c.drop_leg<<','<<c.travel_delta<<','<<c.added_duration<<','
            <<out.verification.objective<<','<<out.verification.G<<','<<out.verification.P<<','
            <<out.stats.placements<<','<<out.stats.quantity_evaluations<<','<<status<<'\n';
        trace.flush();if(!trace)throw std::runtime_error("Joint insertion evidence write failed");
    };
    write({},"initial_verified");
    for(;;) {
        const auto choice=bestRound73Insertion(in,out.routes,options.lambda,out.stats,&options);
        if(out.stats.deadline_reached) {write({},"whole_run_deadline");break;}
        if(!choice.found) {out.stats.exhausted=true;write({},"motif_exhausted");break;}
        auto next=applyRound73Insertion(out.routes,choice);
        auto checked=verifySolution(in,next,options.lambda);
        if(!checked.feasible || !checked.errors.empty() ||
            !checked.original_objective_recomputed ||
            std::fabs(checked.objective-choice.objective)>1e-10 ||
            !(out.verification.objective-checked.objective>improvement))
            throw std::runtime_error("Joint insertion failed independent physical/objective admission");
        out.routes=std::move(next);out.verification=std::move(checked);
        ++out.stats.accepted;
        if(choice.pickup && choice.drop)++out.stats.pairs;
        else if(choice.pickup)++out.stats.single_pickups;else ++out.stats.single_drops;
        if(out.stats.accepted>in.V)throw std::runtime_error("Joint insertion finite-visit invariant failed");
        write(choice,"accepted_verified");
    }
    return out;
}

} // namespace ebrp
