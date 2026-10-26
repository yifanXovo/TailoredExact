#include "HgaTgbcRunner.hpp"
#include "Evaluator.hpp"
#include "Round60Candidates.hpp"
#include "hga_tgbc/HybridGA.h"
#include <cmath>
#include <iostream>
#include <stdexcept>
using namespace ebrp;
static void require(bool value,const char* reason) {
    if(!value)throw std::runtime_error(reason);
}
static Instance fixture() {
    Instance in;in.V=14;in.M=3;in.Q={3,4,5};
    in.initial.assign(15,0);in.target.assign(15,3);in.target[0]=0;
    in.capacity.assign(15,6);in.capacity[0]=0;
    in.weights.assign(15,1.0/14);in.weights[0]=0;in.min_ratio.assign(15,0);
    in.pickup_time=.5;in.drop_time=.5;in.total_time_limit=22;
    std::vector<double> x(15),y(15);
    for(int i=1;i<=14;++i) {in.initial[i]=(i%2)?6:0;x[i]=(i%2)?-3:3;y[i]=.15*i;}
    in.dist.assign(15,std::vector<double>(15));
    for(int i=0;i<=14;++i)for(int j=0;j<=14;++j)in.dist[i][j]=std::hypot(x[i]-x[j],y[i]-y[j]);
    return in;
}
static InstanceData hga(const Instance& in) {
    InstanceData d;d.V=in.V;d.M=in.M;d.Q=in.Q;d.s=in.initial;d.c=in.capacity;
    d.Target=in.target;d.weights=in.weights;d.min_ratio=in.min_ratio;d.dist=in.dist;
    d.total_time_limit=in.total_time_limit;d.load_time_unit=in.pickup_time;
    d.unload_time_unit=in.drop_time;d.MAX_tour_Len=static_cast<int>(in.total_time_limit);
    return d;
}
static void qualify() {
    const auto in=fixture();HgaTgbcOptions opt;opt.seed=20260626u;
    opt.stop_mode="decoded-descent-interroute";opt.pop_size=24;opt.lambda=.15;
    opt.publish_verified_improvements=true;opt.retain_verified_on_log_failure=true;
    const auto first=runHgaTgbcNative(in,opt);const auto second=runHgaTgbcNative(in,opt);
    require(first.found&&first.decoded_descent_complete&&first.decoded_descent_seeds_completed==24,
        "all finite inter-route seeds complete and retain physical witness");
    require(first.decoded_descent_cross_route_enabled&&first.decoded_descent_cross_route_checks>0,
        "real cross-route candidates must be decoded, not only enabled");
    require(first.total_generations==0,"no disguised evolutionary generation quota");
    const auto checked=verifySolution(in,first.routes,opt.lambda);
    require(checked.feasible&&checked.objective_matches&&checked.errors.empty(),
        "cross-route witness respects heterogeneous capacities, original time and one-service semantics");
    require(std::abs(checked.objective-first.verified_objective)<1e-10,"physical objective matches");
    require(canonicalCandidateSerialization(first.routes)==canonicalCandidateSerialization(second.routes)&&
        first.decoded_descent_cross_route_checks==second.decoded_descent_cross_route_checks&&
        first.decoded_descent_cross_route_moves==second.decoded_descent_cross_route_moves,
        "fixed-seed inter-route search is reproducible");
    auto initial=opt;initial.stop_mode="generation-stagnation";initial.fixed_generations=0;
    const auto baseline=runHgaTgbcNative(in,initial);
    require(baseline.found&&first.verified_objective<=baseline.verified_objective+1e-10,
        "best fully decoded initial population is preserved");
    HybridGA_HGS<> cached(hga(in),24,.85,.65,.30,60,4,10,10,opt.lambda,1.0),
        fresh(hga(in),24,.85,.65,.30,60,4,10,10,opt.lambda,1.0);
    for(auto* ga:{&cached,&fresh}) {
        ga->set_seed(opt.seed);ga->set_decoded_descent_only(true);
        ga->set_enable_tail_cross_route(true);ga->set_decoder_compaction_mode(1);
    }
    fresh.set_decode_cache_max_entries(0);cached.run();fresh.run();
    require(cached.completed_decoded_descent()&&fresh.completed_decoded_descent()&&
        cached.get_best_fitness()==fresh.get_best_fitness()&&
        cached.get_best_solution()==fresh.get_best_solution()&&
        cached.get_best_decoded_operations()==fresh.get_best_decoded_operations(),
        "cached and fresh cross-route decoding agree");
    size_t terminal=0,cross_checks=0,cross_moves=0;
    for(const auto& row:cached.get_descent_passes()) {
        require(!row.interrupted&&row.cross_route_evaluations<=row.cross_route_neighbors&&
            row.cross_route_neighbors<=row.neighbors,"cross-route trace counts are consistent");
        if(row.exhausted) {
            ++terminal;require(row.full_evaluations==row.neighbors&&
                row.cross_route_evaluations==row.cross_route_neighbors,"terminal pass exhausts all cross-route candidates");
        }
        if(row.accepted)require(row.fitness_after>row.fitness_before+1e-12,"strict full-decoded improvement");
        if(row.accepted_cross_route)require(row.accepted&&row.cross_route_evaluations>0,"accepted cross-route move was decoded");
        cross_checks+=row.cross_route_evaluations;cross_moves+=row.accepted_cross_route?1:0;
    }
    require(terminal==24&&cross_checks>0,"actual finite cross-route neighborhood was exhausted");
    auto zero_instance=in;zero_instance.initial=zero_instance.target;
    opt.stop_on_verified_zero=true;const auto zero=runHgaTgbcNative(zero_instance,opt);
    require(zero.found&&zero.verified_zero_stop&&!zero.decoded_descent_complete,
        "zero stops without falsely reporting all neighborhoods complete");
    HybridGA_HGS<> expired(hga(in),24);expired.set_decoded_descent_only(true);
    expired.set_enable_tail_cross_route(true);
    expired.set_absolute_deadline(std::chrono::steady_clock::now()-std::chrono::seconds(1));expired.run();
    require(expired.stopped_on_absolute_deadline()&&!expired.completed_decoded_descent()&&
        expired.get_decoder_calls()==0,"whole-run deadline starts no decoder when already expired");
    opt.fixed_generations=1;bool rejected=false;
    try{(void)runHgaTgbcNative(in,opt);}catch(const std::runtime_error&){rejected=true;}
    require(rejected,"inter-route descent rejects generation quotas");
    std::cout<<"Inter-route checks="<<cross_checks<<" accepted moves="<<cross_moves<<"; no optimizer calls\n";
}
int main(){try{qualify();return 0;}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
