#include "Round65Proof.hpp"
#include "HgaTgbcRunner.hpp"
#include "Evaluator.hpp"
#include "PaperK1AmSf.hpp"
#include <filesystem>
#include <iostream>
#include <stdexcept>
using namespace ebrp;
void require(bool b, const char* why) { if (!b) throw std::runtime_error(why); }
int main() { try {
    SolveOptions defaults; configurePaperK1AmSfOverrides(defaults);
    require(!defaults.round65_budget && !defaults.round65_hga_zero_stop && defaults.round65_projection=="off", "stable defaults");
    Round65Budget b;
    require(b.grant(100).work==10 && b.grant(2).seconds==1, "single call and physical reserve");
    b.charge(true,31,31,"a","WORK_LIMIT",b.grant(100));
    require(!b.grant(100).allowed(), "overshoot becomes debt");
    b.charge(false,20,20,"core","OPTIMAL",{});
    require(b.grant(100).work==1 && b.grant(100).seconds==1, "credit only from measured core");
    b.charge(true,1,1,"b","UNKNOWN",b.grant(100));
    require(!b.grant(100).allowed(), "unknown is charged");
    b.charge(false,std::numeric_limits<double>::quiet_NaN(),2,"bad","unknown",{});
    require(!b.grant(100).allowed(), "bad cost stops optional work");

    Instance in; in.V=2; in.M=1; in.Q={5}; in.capacity={0,10,10};
    in.initial={0,5,5}; in.target={0,5,5}; in.weights={0,.5,.5};
    in.min_ratio={0,0,0}; in.dist={{0,1,1},{1,0,1},{1,1,0}};
    in.pickup_time=in.drop_time=1; in.total_time_limit=20;
    HgaTgbcOptions off; off.pop_size=4; off.iterations=1; off.stop_mode="generation-stagnation";
    off.no_improve_generation_limit=2;
    auto legacy=runHgaTgbcNative(in,off);
    auto on=off; on.stop_on_verified_zero=true; on.retain_verified_on_log_failure=true;
    auto zero=runHgaTgbcNative(in,on);
    require(zero.found && zero.verified_zero_stop && zero.total_generations==0 &&
        zero.verified_objective<=1e-12 && legacy.total_generations>=2, "verified initialization zero stops");
    const auto blocker=std::filesystem::temp_directory_path()/"round65_log_blocker";
    { std::ofstream f(blocker); f<<"file"; }
    on.verified_candidate_log_path=blocker/"events.csv";
    auto failed=runHgaTgbcNative(in,on);
    std::filesystem::remove(blocker);
    require(failed.found && failed.verified_zero_stop && !failed.candidate_evidence_persisted, "memory survives audit write failure");
    in.initial={0,1,1}; in.total_time_limit=0;
    auto positive_off=runHgaTgbcNative(in,off);
    on.verified_candidate_log_path.clear();
    auto positive_on=runHgaTgbcNative(in,on);
    require(!positive_on.verified_zero_stop && positive_on.verified_objective>1e-12 &&
        positive_on.total_generations==positive_off.total_generations &&
        positive_on.decoder_calls==positive_off.decoder_calls &&
        positive_on.final_fitness==positive_off.final_fitness, "positive logical prefix and RNG unchanged");
    std::cout<<"Round65 budget and zero reliability passed\n";
    return 0;
} catch(const std::exception& e) { std::cerr<<e.what()<<'\n'; return 1; } }
