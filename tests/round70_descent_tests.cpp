#include "HgaTgbcRunner.hpp"
#include "Evaluator.hpp"
#include "Round60Candidates.hpp"
#include "hga_tgbc/HybridGA.h"
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
using namespace ebrp;
static void require(bool value, const char* reason) {
    if (!value) throw std::runtime_error(reason);
}
static Instance fixture() {
    Instance in;
    in.V=6;in.M=2;in.Q={3,4};in.initial={0,5,0,4,1,3,0};
    in.capacity={0,6,6,6,6,6,6};in.target={0,3,3,3,3,3,3};
    in.weights={0,1.0/6,1.0/6,1.0/6,1.0/6,1.0/6,1.0/6};
    in.min_ratio={0,0,0,0,0,0,0};in.pickup_time=.25;in.drop_time=.75;
    in.total_time_limit=18;
    in.dist.assign(7,std::vector<double>(7));
    for(int i=0;i<=6;++i)for(int j=0;j<=6;++j)in.dist[i][j]=std::abs(i-j);
    return in;
}
static InstanceData hga(const Instance& in) {
    InstanceData d;d.V=in.V;d.M=in.M;d.Q=in.Q;d.s=in.initial;d.c=in.capacity;
    d.Target=in.target;d.weights=in.weights;d.min_ratio=in.min_ratio;d.dist=in.dist;
    d.total_time_limit=in.total_time_limit;d.load_time_unit=in.pickup_time;
    d.unload_time_unit=in.drop_time;d.MAX_tour_Len=static_cast<int>(in.total_time_limit);
    return d;
}
static void qualifiedDescent() {
    const auto in=fixture();
    HgaTgbcOptions opt;opt.seed=20260626u;opt.pop_size=4;opt.lambda=.15;
    opt.stop_mode="decoded-descent";opt.publish_verified_improvements=true;
    opt.retain_verified_on_log_failure=true;
    const auto first=runHgaTgbcNative(in,opt);
    const auto second=runHgaTgbcNative(in,opt);
    require(first.found&&second.found&&first.decoded_descent_complete,
            "all finite seeds must finish and provide a verified witness");
    require(first.total_generations==0&&first.decoded_descent_seeds_completed==4,
            "descent is not a renamed HGA generation quota");
    const auto v=verifySolution(in,first.routes,opt.lambda);
    require(v.feasible&&v.objective_matches&&v.errors.empty(),"independent physical witness");
    require(std::abs(v.objective-first.verified_objective)<1e-10,
            "physical objective equals retained value");
    require(canonicalCandidateSerialization(first.routes)==canonicalCandidateSerialization(second.routes)&&
            first.decoded_descent_passes==second.decoded_descent_passes&&
            first.decoded_descent_checks==second.decoded_descent_checks,
            "fixed seed is reproducible without choosing a favorable repeat");
    auto initial=opt;initial.stop_mode="generation-stagnation";initial.fixed_generations=0;
    const auto initial_only=runHgaTgbcNative(in,initial);
    require(initial_only.found&&first.verified_objective<=initial_only.verified_objective+1e-10,
            "descent preserves the best already evaluated seed");

    HybridGA_HGS<> cached(hga(in),4),uncached(hga(in),4);
    for(auto* ga:{&cached,&uncached}) {
        ga->set_seed(opt.seed);ga->set_decoded_descent_only(true);
        ga->set_decoder_compaction_mode(1);
    }
    uncached.set_decode_cache_max_entries(0);
    cached.run();uncached.run();
    require(cached.completed_decoded_descent()&&uncached.completed_decoded_descent(),
            "cached and fresh complete decodes finish");
    require(cached.get_best_solution()==uncached.get_best_solution()&&
            cached.get_best_decoded_operations()==uncached.get_best_decoded_operations()&&
            cached.get_best_fitness()==uncached.get_best_fitness(),
            "cached and fresh decode paths give identical completed witnesses");
    size_t exhausted=0;
    for(const auto& row:cached.get_descent_passes()) {
        require(!row.interrupted,"no interruption in a completed finite descent");
        require(row.accepted!=row.exhausted,"each completed pass improves or exhausts its neighborhood");
        if(row.exhausted) {
            ++exhausted;
            require(row.full_evaluations==row.neighbors,"all neighbors are checked before declaring exhaustion");
        }
        if(row.accepted)require(row.fitness_after>row.fitness_before+1e-12,
            "strict decoded-objective gain, not proxy gain, accepts the move");
    }
    require(exhausted==4,"one exhausted terminal neighborhood per seed");
}
static void stopsAndPersistence() {
    auto in=fixture();in.initial=in.target;
    HgaTgbcOptions opt;opt.pop_size=4;opt.stop_mode="decoded-descent";
    opt.stop_on_verified_zero=true;opt.retain_verified_on_log_failure=true;
    const auto zero=runHgaTgbcNative(in,opt);
    require(zero.found&&zero.verified_zero_stop&&!zero.decoded_descent_complete&&
            zero.decoded_descent_seeds_completed==0&&zero.total_generations==0,
            "verified zero stops before claiming all seed neighborhoods exhausted");
    const auto blocker=std::filesystem::temp_directory_path()/
        ("round70_descent_log_blocker_" + std::to_string(
            std::chrono::steady_clock::now().time_since_epoch().count()));
    require(!std::filesystem::exists(blocker),"temporary blocker must be new");
    {std::ofstream file(blocker);file<<"file";}
    opt.generation_log_path=blocker/"trace.csv";
    const auto failed_log=runHgaTgbcNative(in,opt);
    std::filesystem::remove(blocker);
    require(failed_log.found&&failed_log.verified_zero_stop&&!failed_log.candidate_evidence_persisted,
            "verified in-memory witness survives a trajectory persistence failure");
    opt.generation_log_path.clear();opt.fixed_generations=3;
    bool rejected=false;
    try{(void)runHgaTgbcNative(in,opt);}catch(const std::runtime_error&){rejected=true;}
    require(rejected,"no generation resource quota is permitted for decoded descent");
    HybridGA_HGS<> expired(hga(fixture()),4);
    expired.set_decoded_descent_only(true);
    expired.set_absolute_deadline(std::chrono::steady_clock::now()-std::chrono::seconds(1));
    expired.run();
    require(expired.stopped_on_absolute_deadline()&&!expired.completed_decoded_descent()&&
            expired.get_decoder_calls()==0,"an expired whole-run deadline starts no decoder");
}
int main(){try{qualifiedDescent();stopsAndPersistence();
    std::cout<<"Decoded descent qualification passed; no optimizer calls\n";return 0;
}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
