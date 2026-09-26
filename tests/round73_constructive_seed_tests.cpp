#include "HgaTgbcRunner.hpp"
#include "Round73JointInsertion.hpp"
#include "Evaluator.hpp"
#include "hga_tgbc/HybridGA.h"
#include <cmath>
#include <iostream>
#include <stdexcept>
using namespace ebrp;
static void require(bool ok,const char* reason){if(!ok)throw std::runtime_error(reason);}
static Instance fixture(){
    Instance in;in.V=14;in.M=3;in.Q={3,4,5};
    in.initial.assign(15,0);in.target.assign(15,3);in.target[0]=0;
    in.capacity.assign(15,6);in.weights.assign(15,1.0/14);in.weights[0]=0;
    in.min_ratio.assign(15,0);in.pickup_time=.5;in.drop_time=.5;in.total_time_limit=22;
    std::vector<double>x(15),y(15);
    for(int i=1;i<=14;++i){in.initial[i]=i%2?6:0;x[i]=i%2?-3:3;y[i]=.15*i;}
    in.dist.assign(15,std::vector<double>(15));
    for(int i=0;i<=14;++i)for(int j=0;j<=14;++j)in.dist[i][j]=std::hypot(x[i]-x[j],y[i]-y[j]);
    return in;
}
static InstanceData hga(const Instance& in){
    InstanceData d;d.V=in.V;d.M=in.M;d.Q=in.Q;d.s=in.initial;d.c=in.capacity;
    d.Target=in.target;d.weights=in.weights;d.min_ratio=in.min_ratio;d.dist=in.dist;
    d.total_time_limit=in.total_time_limit;d.load_time_unit=in.pickup_time;d.unload_time_unit=in.drop_time;
    d.MAX_tour_Len=static_cast<int>(in.total_time_limit);return d;
}
int main(){try{
    const auto in=fixture();SolveOptions construction;construction.lambda=.15;
    const auto ji=runRound73JointInsertion(in,construction);
    HgaTgbcOptions opt;opt.lambda=.15;opt.stop_mode="decoded-descent-interroute";
    opt.pop_size=24;opt.seed=20260626u;opt.publish_verified_improvements=true;
    opt.retain_verified_on_log_failure=true;
    const auto baseline=runHgaTgbcNative(in,opt);
    opt.joint_constructive_seed=true;opt.joint_constructive_routes=ji.routes;
    const auto seeded=runHgaTgbcNative(in,opt);
    auto solo_opt=opt;
    solo_opt.round88_constructive_only_descent=true;
    const auto solo=runHgaTgbcNative(in,solo_opt);
    require(solo.found&&solo.decoded_descent_complete&&solo.decoded_descent_seeds_completed==1,
        "Round88 constructive-only ablation completes exactly one descent path");
    const auto solo_physical=verifySolution(in,solo.routes,solo_opt.lambda);
    require(solo_physical.feasible&&solo_physical.objective_matches&&solo_physical.errors.empty()&&
        std::fabs(solo_physical.objective-solo.verified_objective)<1e-10,
        "Round88 single-path native witness preserves original physical verification");
    require(seeded.verified_objective<=solo.verified_objective+1e-10,
        "default 25-path ENS-C search retains the single constructive path");
    auto invalid_solo=solo_opt;
    invalid_solo.joint_constructive_seed=false;
    bool solo_rejected=false;
    try{runHgaTgbcNative(in,invalid_solo);}catch(const std::exception&){solo_rejected=true;}
    require(solo_rejected,"Round88 cannot run without the verified constructive seed");
    invalid_solo=solo_opt;invalid_solo.stop_mode="decoded-descent";
    solo_rejected=false;
    try{runHgaTgbcNative(in,invalid_solo);}catch(const std::exception&){solo_rejected=true;}
    require(solo_rejected,"Round88 rejects an incompatible descent mode");
    require(seeded.found&&seeded.decoded_descent_complete&&seeded.decoded_descent_seeds_completed==25,
        "one constructive seed actually completes the same finite descent");
    const auto physical=verifySolution(in,seeded.routes,opt.lambda);
    require(physical.feasible&&physical.errors.empty()&&std::fabs(physical.objective-seeded.verified_objective)<1e-10,
        "constructive-seeded native output is physically verified");
    require(seeded.verified_objective<=baseline.verified_objective+1e-10,
        "completed unchanged random seed search retains its prior UB quality");
    require(seeded.total_generations==0,"no evolutionary generations or internal timer replacement");
    HybridGA_HGS<> plain(hga(in),24,.85,.65,.30,60,4,10,10,.15,1),
        extra(hga(in),24,.85,.65,.30,60,4,10,10,.15,1),
        uncached(hga(in),24,.85,.65,.30,60,4,10,10,.15,1),
        only(hga(in),24,.85,.65,.30,60,4,10,10,.15,1);
    HybridGA_HGS<> missing_seed(hga(in),24);
    missing_seed.set_decoded_descent_only(true);
    solo_rejected=false;
    try{missing_seed.set_constructive_only_descent(true);}catch(const std::exception&){solo_rejected=true;}
    require(solo_rejected,"GA itself rejects constructive-only descent without an extra seed");
    std::vector<std::vector<int>> order(in.M);
    for(int i=1;i<=in.V;++i)order[0].push_back(i);
    for(auto* ga:{&plain,&extra,&uncached,&only}){
        ga->set_seed(20260626u);ga->set_decoded_descent_only(true);
        ga->set_enable_tail_cross_route(true);ga->set_decoder_compaction_mode(1);
    }
    extra.set_extra_descent_seed(order);uncached.set_extra_descent_seed(order);
    only.set_extra_descent_seed(order);only.set_constructive_only_descent(true);
    uncached.set_decode_cache_max_entries(0);plain.run();extra.run();uncached.run();only.run();
    const auto& a=plain.get_descent_passes();const auto& b=extra.get_descent_passes();
    require(b.size()>a.size()&&extra.get_descent_seeds_completed()==25,"extra seed adds actual terminal passes");
    for(std::size_t i=0;i<a.size();++i){
        const auto& x=a[i];const auto& y=b[i];
        require(x.seed==y.seed&&x.pass==y.pass&&x.neighbors==y.neighbors&&x.full_evaluations==y.full_evaluations&&
            x.cross_route_neighbors==y.cross_route_neighbors&&x.cross_route_evaluations==y.cross_route_evaluations&&
            x.accepted_cross_route==y.accepted_cross_route&&x.accepted==y.accepted&&x.exhausted==y.exhausted&&
            x.interrupted==y.interrupted&&x.fitness_before==y.fitness_before&&x.fitness_after==y.fitness_after,
            "first24 full logical descent paths are unchanged by the appended seed");
    }
    const auto& c=only.get_descent_passes();
    require(only.completed_decoded_descent()&&only.get_descent_seeds_completed()==1,
        "constructive-only direct GA completes one finite path");
    std::size_t constructive_passes=0;
    for(const auto& row:b)if(row.seed==25){
        require(constructive_passes<c.size(),"Round88 path has all ENS-C constructive passes");
        const auto& x=c[constructive_passes++];
        require(x.seed==1&&x.neighbors==row.neighbors&&x.full_evaluations==row.full_evaluations&&
            x.cross_route_neighbors==row.cross_route_neighbors&&x.cross_route_evaluations==row.cross_route_evaluations&&
            x.accepted_cross_route==row.accepted_cross_route&&x.accepted==row.accepted&&x.exhausted==row.exhausted&&
            x.fitness_before==row.fitness_before&&x.fitness_after==row.fitness_after,
            "Round88 preserves every logical pass of ENS-C's constructive path");
    }
    require(constructive_passes==c.size()&&constructive_passes>0,
        "Round88 and ENS-C constructive paths have identical finite length");
    std::size_t seed_checks=0;int accepted=0;
    for(const auto& row:b)if(row.seed==25){seed_checks+=row.full_evaluations;accepted+=row.accepted;}
    require(seed_checks>0,"constructive seed must be descended, not only merged as another UB");
    require(extra.get_best_fitness()==uncached.get_best_fitness()&&
        extra.get_best_solution()==uncached.get_best_solution()&&
        extra.get_best_decoded_operations()==uncached.get_best_decoded_operations(),
        "cache changes no seeded mathematical decoding result");
    bool rejected=false;auto duplicate=order;duplicate[0].push_back(1);
    try{extra.set_extra_descent_seed(duplicate);}catch(const std::exception&){rejected=true;}
    require(rejected,"duplicate constructive station is rejected");
    rejected=false;auto missing=order;missing[0].pop_back();
    try{extra.set_extra_descent_seed(missing);}catch(const std::exception&){rejected=true;}
    require(rejected,"missing constructive station is rejected");
    rejected=false;HgaTgbcOptions invalid=opt;invalid.stop_mode="generation-stagnation";
    try{runHgaTgbcNative(in,invalid);}catch(const std::exception&){rejected=true;}
    require(rejected,"constructive seed cannot silently alter the historical evolutionary path");
    extra.set_absolute_deadline(std::chrono::steady_clock::now()-std::chrono::seconds(1));
    extra.run();
    require(!extra.completed_decoded_descent()&&extra.get_descent_seeds_completed()==0,
        "whole-run interruption never masquerades as25-seed exhaustion");
    std::cout<<"Round73 seed checks: preserved24_seed_passes="<<a.size()<<", extra_seed_checks="<<seed_checks
        <<", extra_seed_accepted="<<accepted<<", actual_seeds=25\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
