#include "Round61Candidates.hpp"
#include "Evaluator.hpp"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <limits>
#include <map>
#include <stdexcept>
#include <tuple>

namespace ebrp {
namespace {
using Clock = std::chrono::steady_clock;
double elapsed(Clock::time_point t) {
    return std::chrono::duration<double>(Clock::now()-t).count();
}
struct State {
    RoutePlan route;
    int load = 0, pickup = 0;
    double travel = 0;
};
struct Move {
    int k = -1, a = 0, b = 0, direction = -1, qmax = 0, q = 0;
    double travel = 0, score = 0, F = std::numeric_limits<double>::infinity();
};
std::vector<RoutePlan> materialize(const std::vector<State>& states) {
    std::vector<RoutePlan> result;
    for (const auto& s: states) if (!s.route.operations.empty()) result.push_back(s.route);
    return result;
}
Round61CandidateTrace checkpoint(const Instance& in, double lambda,
    const VerifiedBrpCandidate& c, int round, long long eval, int blocks, double sec) {
    Round61CandidateTrace t;
    t.round=round; t.evaluations=eval; t.blocks=blocks; t.seconds=sec;
    t.F=c.objective; t.G=c.G; t.P=c.P;
    const auto v=verifySolution(in,c.routes,lambda);
    for (const auto& r:c.routes) for (const auto& o:r.operations) {
        ++t.stations; t.pickup+=o.pickup; t.drop+=o.drop;
    }
    for(double d:v.route_duration) t.maximum_duration=std::max(t.maximum_duration,d);
    return t;
}
}

std::shared_ptr<Round61CandidateSession> prepareRound61Candidate(
    const Instance& in,const SolveOptions& options,const std::filesystem::path& path) {
    auto session=std::make_shared<Round61CandidateSession>();
    session->mode=options.round61_candidate_mode;
    if(session->mode=="off") return session;
    session->construction_attempted=true;
    const auto start=Clock::now();
    VerifiedCandidateStore store;
    store.consider(in,options.lambda,{},"empty_fallback","original_problem");
    try {
        auto prefix=constructRound61Prefix(in,options.lambda,&options,true,path);
        session->source_snapshot_sha256=prefix.retained_candidate_sha256;
        session->evidence_persisted=prefix.candidate_evidence_persisted;
        if(prefix.found) store.consider(in,options.lambda,
            normalizeRound61Routes(in,options.lambda,prefix.routes),"PREFIX","original_problem");
        else session->failure_reason="prefix_no_verified_result";
    } catch(const std::exception& e) { session->failure_reason=e.what(); }
    session->archive=store.best();
    session->construction_seconds=elapsed(start);
    try {
        std::filesystem::create_directories(path);
        writeRound61Witness(path/"archive_witness.json",in,options.lambda,session->archive);
        std::ofstream f(path/"archive_state.json"); f<<std::setprecision(17)
            <<"{\"mode\":\""<<session->mode<<"\",\"F\":"<<session->archive.objective
            <<",\"construction_seconds\":"<<session->construction_seconds
            <<",\"evidence_persisted\":"<<session->evidence_persisted
            <<",\"construction_failed\":"<<!session->failure_reason.empty()
            <<",\"source_snapshot_sha256\":\""<<session->source_snapshot_sha256
            <<"\",\"normalized_snapshot_sha256\":\""<<session->archive.content_sha256<<"\"}\n";
        if(!f) session->evidence_persisted=false;
    } catch(...) { session->evidence_persisted=false; }
    return session;
}

std::vector<RoutePlan> normalizeRound61Routes(const Instance& in,double lambda,
    const std::vector<RoutePlan>& routes) {
    VerifiedCandidateStore before;
    if(!before.consider(in,lambda,routes,"before_normalization","original_problem"))
        throw std::invalid_argument("normalization requires verified complete routes");
    std::map<int,std::vector<int>> classes;
    for(int k=0;k<in.M;++k) classes[in.Q[k]].push_back(k);
    std::vector<RoutePlan> out;
    for(const auto& c:classes) {
        std::vector<RoutePlan> used;
        for(int k:c.second) for(const auto& route:routes)
            if(route.vehicle==k && !route.operations.empty()) used.push_back(route);
        std::stable_sort(used.begin(),used.end(),[](const RoutePlan& a,const RoutePlan& b) {
            return a.operations.size()>b.operations.size();
        });
        for(size_t j=0;j<used.size();++j) { used[j].vehicle=c.second[j]; out.push_back(used[j]); }
    }
    std::sort(out.begin(),out.end(),[](const RoutePlan& a,const RoutePlan& b){return a.vehicle<b.vehicle;});
    VerifiedCandidateStore after;
    if(!after.consider(in,lambda,out,"after_normalization","original_problem") ||
       before.best().final_inventory!=after.best().final_inventory ||
       std::abs(before.best().objective-after.best().objective)>1e-10)
        throw std::runtime_error("normalization changed physical witness");
    return out;
}

ObjectiveParts round61Increment(const Instance& in, const std::vector<int>& y,
    const ObjectiveParts& old, double lambda, int a, int da, int b, int db) {
    if (a <= 0 || a > in.V || b < 0 || b > in.V || a == b ||
        y.size()!=in.initial.size() || y[a]+da<0 || y[a]+da>in.capacity[a] ||
        (b && (y[b]+db<0 || y[b]+db>in.capacity[b])))
        throw std::invalid_argument("invalid two-inventory increment");
    ObjectiveParts out=old;
    const double ra=double(y[a])/in.target[a], na=double(y[a]+da)/in.target[a];
    const double rb=b?double(y[b])/in.target[b]:0, nb=b?double(y[b]+db)/in.target[b]:0;
    out.S += na-ra+nb-rb;
    out.H += b ? std::abs(na-nb)-std::abs(ra-rb) : 0;
    for(int j=1;j<=in.V;++j) if(j!=a && j!=b) {
        double r=double(y[j])/in.target[j];
        out.H+=std::abs(na-r)-std::abs(ra-r);
        if(b) out.H+=std::abs(nb-r)-std::abs(rb-r);
    }
    out.P+=in.weights[a]*(std::abs(na-1)-std::abs(ra-1));
    if(b) out.P+=in.weights[b]*(std::abs(nb-1)-std::abs(rb-1));
    // Follow the original exact S=0 convention, avoid cancellation at zero.
    long long sum=static_cast<long long>(da)+db;
    for(int j=1;j<=in.V;++j) sum+=y[j];
    if(sum==0) { out.S=0; out.H=0; }
    out.G=out.S>0 ? std::max(0.0,out.H)/(in.V*out.S) : 0;
    out.objective=out.G+lambda*out.P;
    return out;
}

Round61BlockResult constructRound61Block(const Instance& in, double lambda,
    const Round61BlockOptions& options) {
    const auto start=Clock::now();
    Round61BlockResult out;
    if(options.maximum_rounds<0 || options.pairs_per_round<=0 ||
       options.singles_per_round<0 || options.quantities_per_round<
       options.pairs_per_round+options.singles_per_round || options.safety_seconds<=0)
        throw std::invalid_argument("invalid BLOCK logical budget");
    std::vector<int> y=in.initial;
    auto parts=computeObjectiveParts(in,y,lambda);
    std::vector<bool> used(in.V+1,false);
    std::vector<State> states(in.M);
    for(int k=0;k<in.M;++k) { states[k].route.vehicle=k; states[k].route.nodes={0,0}; }
    VerifiedCandidateStore store;
    store.consider(in,lambda,{},"BLOCK-empty","original_problem");
    out.trajectory.push_back(checkpoint(in,lambda,store.best(),0,0,0,elapsed(start)));
    const double c=in.pickup_time+in.drop_time;
    out.stop_reason="logical_round_limit";
    for(int round=1; round<=options.maximum_rounds; ++round) {
        if(elapsed(start)>=options.safety_seconds) { out.stop_reason="safety_deadline"; break; }
        const auto scan=Clock::now();
        std::vector<Move> pairs,singles;
        // Each station pair first chooses its cheapest feasible vehicle. Thus
        // capacity/vehicle numbering never monopolizes the quantity budget.
        for(int a=1;a<=in.V;++a) if(!used[a]) {
            for(int b=0;b<=in.V;++b) if(b!=a && (!b || !used[b])) {
                if(b && (!y[a] || y[b]>=in.capacity[b])) continue;
                for(int direction: {-1,1}) {
                    if(b && direction==1) continue;
                    if(!b && ((direction==-1 && !y[a]) ||
                              (direction==1 && y[a]>=in.capacity[a]))) continue;
                    Move chosen;
                    for(int k=0;k<in.M;++k) {
                        const auto& s=states[k];
                        const int last=s.route.nodes[s.route.nodes.size()-2];
                        const double travel=s.travel-in.dist[last][0]+in.dist[last][a]+
                            (b?in.dist[a][b]+in.dist[b][0]:in.dist[a][0]);
                        int qmax=direction==-1 ? std::min(y[a],in.Q[k]-s.load)
                                               : std::min(in.capacity[a]-y[a],s.load);
                        if(b) qmax=std::min(qmax,in.capacity[b]-y[b]);
                        if(c>0 && direction==-1) qmax=std::min(qmax,int(std::floor(
                            (in.total_time_limit-travel-c*s.pickup+1e-9)/c)));
                        if(qmax<=0 || travel+c*s.pickup>in.total_time_limit+1e-9) continue;
                        if(chosen.k<0 || std::make_tuple(travel-s.travel,-qmax,k)<
                            std::make_tuple(chosen.travel-states[chosen.k].travel,-chosen.qmax,chosen.k)) {
                            chosen.k=k; chosen.a=a; chosen.b=b; chosen.direction=direction;
                            chosen.qmax=qmax; chosen.travel=travel;
                        }
                    }
                    if(chosen.k<0) continue;
                    const double ra=double(y[a])/in.target[a];
                    // Cheap structure ranking, not a correctness/convexity claim.
                    const double contrast=b ? ra-double(y[b])/in.target[b]
                                             : direction*(1-ra);
                    chosen.score=contrast/(1+std::max(0.0,chosen.travel-
                        states[chosen.k].travel)/std::max(1.0,in.total_time_limit));
                    (b?pairs:singles).push_back(chosen);
                    if(b) ++out.cheap_pairs;
                }
            }
        }
        auto rank=[](const Move& a,const Move& b) {
            return std::make_tuple(-a.score,a.travel,-a.qmax,a.a,a.b,a.k)<
                   std::make_tuple(-b.score,b.travel,-b.qmax,b.a,b.b,b.k);
        };
        std::sort(pairs.begin(),pairs.end(),rank); std::sort(singles.begin(),singles.end(),rank);
        pairs.resize(std::min(pairs.size(),size_t(options.pairs_per_round)));
        singles.resize(std::min(singles.size(),size_t(options.singles_per_round)));
        out.evaluated_pairs+=pairs.size();
        pairs.insert(pairs.end(),singles.begin(),singles.end());
        out.scan_seconds+=elapsed(scan);
        const auto eval=Clock::now();
        Move best;
        int evaluations=0;
        bool safety=false;
        // Quantity-major round robin: every shortlisted block receives q=1
        // before any receives q=2. No unproved maximum-q shortcut.
        for(int q=1; evaluations<options.quantities_per_round; ++q) {
            bool any=false;
            for(auto& m:pairs) {
                if(q>m.qmax) continue;
                if(evaluations>=options.quantities_per_round) break;
                if(elapsed(start)>=options.safety_seconds) { safety=true; break; }
                any=true;
                auto p=round61Increment(in,y,parts,lambda,m.a,m.direction*q,m.b,m.b?q:0);
                ++evaluations;
                const auto key=std::make_tuple(p.objective,m.travel-states[m.k].travel,m.a,m.b,m.k,q);
                const auto prior=std::make_tuple(best.F,best.k<0?0:best.travel-states[best.k].travel,
                                                best.a,best.b,best.k,best.q);
                if(best.k<0 || key<prior) { best=m; best.q=q; best.F=p.objective; }
            }
            if(!any || safety) break;
        }
        out.quantity_evaluations+=evaluations;
        out.evaluation_seconds+=elapsed(eval);
        if(best.k<0 || best.F>=parts.objective-1e-10*std::max(1.0,std::abs(parts.objective))) {
            out.stop_reason=safety?"safety_deadline":"no_strict_complete_move_improvement"; break;
        }
        const auto accept=Clock::now();
        auto& s=states[best.k];
        auto append=[&](int station,int pickup,int drop) {
            s.route.nodes.insert(s.route.nodes.end()-1,station);
            s.route.operations.push_back({station,pickup,drop});
            s.load+=pickup-drop; s.pickup+=pickup;
            y[station]+=drop-pickup; used[station]=true;
        };
        append(best.a,best.direction==-1?best.q:0,best.direction==1?best.q:0);
        if(best.b) { append(best.b,0,best.q); ++out.completed_blocks; }
        else ++out.accepted_singles;
        s.travel=best.travel;
        parts=computeObjectiveParts(in,y,lambda);
        // Only independently verified complete snapshots are published.
        if(!store.consider(in,lambda,materialize(states),"BLOCK","original_problem",round,elapsed(start))) {
            out.stop_reason="independent_verifier_rejected_return_last_legal"; break;
        }
        out.accept_seconds+=elapsed(accept);
        out.trajectory.push_back(checkpoint(in,lambda,store.best(),round,
            out.quantity_evaluations,out.completed_blocks,elapsed(start)));
        if(safety) { out.stop_reason="safety_deadline"; break; }
    }
    out.candidate=store.best();
    for(const auto& v:store.observations()) out.verification_seconds+=v.verification_seconds;
    out.seconds=elapsed(start); out.candidate.generation_seconds=out.seconds;
    return out;
}

HgaTgbcResult constructRound61Prefix(const Instance& in,double lambda,
    const SolveOptions* process,bool observer,const std::filesystem::path& directory) {
    HgaTgbcOptions o;
    o.lambda=lambda; o.fixed_generations=16; o.max_time_seconds=30;
    o.stop_mode="fixed-prefix"; o.publish_verified_improvements=observer;
    o.retain_verified_on_log_failure=true; o.process_options=process;
    if(!directory.empty()) {
        o.generation_log_path=directory/"prefix_generations.csv";
        o.verified_candidate_log_path=directory/"prefix_events.csv";
    }
    return runHgaTgbcNative(in,o);
}

Round61BlockResult repairRound61Block(const Instance& in,double lambda,
    const VerifiedBrpCandidate& input,const Round61BlockOptions& o) {
    const auto start=Clock::now();
    Round61BlockResult out;
    VerifiedCandidateStore store;
    if(!store.consider(in,lambda,input.routes,"BLOCK-REPAIR-input","original_problem"))
        throw std::invalid_argument("repair requires legal complete input");
    const auto input_routes=input.routes;
    std::vector<int> stations;
    for(const auto& r:input_routes) for(const auto& s:r.operations) stations.push_back(s.station);
    std::sort(stations.begin(),stations.end());
    out.stop_reason="logical_round_limit";
    for(int round=1;round<=std::min(16,o.maximum_rounds);++round) {
        if(elapsed(start)>=o.safety_seconds) { out.stop_reason="safety_deadline"; break; }
        const auto scan=Clock::now();
        const auto y=store.best().final_inventory;
        const auto parts=computeObjectiveParts(in,y,lambda);
        std::vector<Move> pairs;
        for(int a:stations) for(int b:stations) if(a!=b && y[a]>0 && y[b]<in.capacity[b]) {
            Move m; m.a=a; m.b=b; m.qmax=std::min(y[a],in.capacity[b]-y[b]);
            m.score=double(y[a])/in.target[a]-double(y[b])/in.target[b];
            pairs.push_back(m); ++out.cheap_pairs;
        }
        std::sort(pairs.begin(),pairs.end(),[](const Move& a,const Move& b) {
            return std::make_tuple(-a.score,a.a,a.b)<std::make_tuple(-b.score,b.a,b.b);
        });
        pairs.resize(std::min(pairs.size(),size_t(o.pairs_per_round)));
        out.evaluated_pairs+=pairs.size(); out.scan_seconds+=elapsed(scan);
        double bestF=parts.objective;
        std::vector<RoutePlan> best;
        int evaluations=0;
        const auto eval=Clock::now();
        for(int q=1; evaluations<o.quantities_per_round && elapsed(start)<o.safety_seconds;++q) {
            bool any=false;
            for(const auto& m:pairs) {
                if(q>m.qmax || evaluations>=o.quantities_per_round) continue;
                any=true; ++evaluations;
                auto delta=round61Increment(in,y,parts,lambda,m.a,-q,m.b,q);
                if(delta.objective>=bestF-1e-10) continue;
                // A fixed template permits removed zero services to reappear
                // in their original position, never duplicates/split services.
                auto next=y; next[m.a]-=q; next[m.b]+=q;
                std::vector<RoutePlan> routes;
                for(const auto& r:input_routes) {
                    RoutePlan rebuilt; rebuilt.vehicle=r.vehicle; rebuilt.nodes={0};
                    for(int i:r.nodes) if(i && next[i]!=in.initial[i]) {
                        rebuilt.nodes.push_back(i);
                        rebuilt.operations.push_back({i,std::max(0,in.initial[i]-next[i]),
                                                       std::max(0,next[i]-in.initial[i])});
                    }
                    rebuilt.nodes.push_back(0);
                    if(!rebuilt.operations.empty()) routes.push_back(std::move(rebuilt));
                }
                const auto check=Clock::now();
                const auto v=verifySolution(in,routes,lambda);
                out.verification_seconds+=elapsed(check);
                if(v.feasible && std::abs(v.objective-delta.objective)<=1e-8) {
                    bestF=v.objective; best=std::move(routes);
                }
            }
            if(!any) break;
        }
        out.quantity_evaluations+=evaluations; out.evaluation_seconds+=elapsed(eval);
        if(bestF>=parts.objective-1e-10) { out.stop_reason="no_strict_feasible_quantity_repair"; break; }
        const auto accept=Clock::now();
        if(!store.consider(in,lambda,best,"BLOCK-REPAIR","original_problem",round,elapsed(start))) {
            out.stop_reason="verification_failed_last_legal_retained"; break;
        }
        ++out.completed_blocks; out.accept_seconds+=elapsed(accept);
        out.trajectory.push_back(checkpoint(in,lambda,store.best(),round,out.quantity_evaluations,
            out.completed_blocks,elapsed(start)));
    }
    out.candidate=store.best(); out.seconds=elapsed(start);
    return out;
}

void writeRound61Witness(const std::filesystem::path& path,const Instance& in,
    double lambda,const VerifiedBrpCandidate& candidate) {
    if(!candidate.verified) throw std::invalid_argument("unverified candidate export");
    const auto v=verifySolution(in,candidate.routes,lambda);
    if(!v.feasible || std::abs(v.objective-candidate.objective)>1e-8)
        throw std::runtime_error("candidate snapshot mismatch");
    std::ofstream f(path); f<<std::setprecision(17);
    f<<"{\"source\":\""<<candidate.source<<"\",\"sha256\":\""<<candidate.content_sha256
     <<"\",\"F\":"<<v.objective<<",\"G\":"<<v.G<<",\"P\":"<<v.P<<",\"inventory\":[";
    for(size_t i=0;i<v.final_inventory.size();++i) f<<(i?",":"")<<v.final_inventory[i];
    f<<"],\"routes\":[";
    for(size_t k=0;k<candidate.routes.size();++k) {
        const auto& r=candidate.routes[k];
        f<<(k?",":"")<<"{\"vehicle\":"<<r.vehicle<<",\"duration\":"<<v.route_duration[r.vehicle]
         <<",\"nodes\":[";
        for(size_t i=0;i<r.nodes.size();++i) f<<(i?",":"")<<r.nodes[i];
        f<<"],\"operations\":[";
        for(size_t i=0;i<r.operations.size();++i) {
            const auto& o=r.operations[i]; f<<(i?",":"")<<"["<<o.station<<","<<o.pickup<<","<<o.drop<<"]";
        }
        f<<"]}";
    }
    f<<"]}\n";
    if(!f) throw std::runtime_error("witness write failed (memory candidate remains valid)");
}
} // namespace ebrp
