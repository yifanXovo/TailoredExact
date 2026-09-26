#include "Parser.hpp"
#include "Evaluator.hpp"
#include "Round73JointInsertion.hpp"
#include "Round61Candidates.hpp"
#include "ProcessPhaseLedger.hpp"
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
using namespace ebrp;
int main(int argc,char** argv) {
 try {
    SolveOptions opt;opt.process_start_time_valid=true;
    opt.process_start_time=std::chrono::steady_clock::now();
    opt.process_wall_time_limit=30;opt.process_shutdown_margin_seconds=1;
    if(argc!=3)throw std::runtime_error("diagnostic requires role and fresh output directory");
    Instance in;std::vector<RoutePlan> routes;
    if(std::string(argv[1])=="D6") {in=parseInstanceFile("E:\\codes\\ExactEBRP-round66\\reference\\citibike443-regional-v1\\instances\\V30\\cb443_V30_compact_r1_shortage_M03_Q30.txt",18000,60.0,60.0);opt.lambda=0.15;routes={{0,{0,16,30,0},{{16,9,0},{30,0,9}}},{1,{0,18,22,7,24,1,25,17,29,26,13,0},{{18,11,0},{22,0,5},{7,6,0},{24,8,0},{1,0,6},{25,0,10},{17,8,0},{29,7,0},{26,0,11},{13,0,8}}},{2,{0,10,27,14,5,6,15,21,2,19,4,12,3,28,20,11,9,23,8,0},{{10,10,0},{27,8,0},{14,6,0},{5,0,5},{6,0,7},{15,8,0},{21,0,6},{2,0,6},{19,8,0},{4,8,0},{12,0,5},{3,6,0},{28,5,0},{20,0,18},{11,0,5},{9,11,0},{23,0,11},{8,0,7}}}};}
    else if(std::string(argv[1])=="D7") {in=parseInstanceFile("E:\\codes\\ExactEBRP-round66\\reference\\citibike443-regional-v1\\instances\\V50\\cb443_V50_regional_r1_shortage_M04_Q30.txt",18000,60.0,60.0);opt.lambda=0.15;routes={{0,{0,14,47,38,20,19,50,46,22,1,35,15,45,32,48,21,5,43,0},{{14,7,0},{47,0,5},{38,9,0},{20,0,4},{19,13,0},{50,0,16},{46,13,0},{22,0,17},{1,7,0},{35,15,0},{15,7,0},{45,0,7},{32,0,7},{48,15,0},{21,0,19},{5,6,0},{43,0,17}}},{1,{0,6,24,10,4,34,36,31,16,42,37,13,2,39,12,49,23,27,7,17,8,41,28,26,0},{{6,7,0},{24,6,0},{10,6,0},{4,0,7},{34,0,6},{36,9,0},{31,4,0},{16,5,0},{42,5,0},{37,0,4},{13,5,0},{2,0,5},{39,0,6},{12,5,0},{49,4,0},{23,0,7},{27,5,0},{7,0,4},{17,0,6},{8,0,9},{41,0,6},{28,6,0},{26,0,7}}},{2,{0,30,29,9,11,44,25,0},{{30,8,0},{29,7,0},{9,9,0},{11,0,10},{44,0,8},{25,0,6}}},{3,{0,0},{}}};}
    else throw std::runtime_error("undeclared diagnostic role");
    std::filesystem::path out(argv[2]);
    auto verification=verifySolution(in,routes,opt.lambda);
    if(!verification.feasible||!verification.errors.empty())throw std::runtime_error("invalid diagnostic input");
    const double initial=verification.objective;
    auto snapshot=[&](const char* name) {
        VerifiedCandidateStore store;
        if(!store.consider(in,opt.lambda,routes,"round76_fixed_witness_diagnosis","original_problem"))
            throw std::runtime_error("diagnostic snapshot verification failed");
        writeRound61Witness(out/name,in,opt.lambda,store.best());
    };
    snapshot("initial.json");
    Round73InsertionStats stats;
    std::ofstream trace(out/"trace.csv");
    trace<<"step,process_seconds,vehicle,pickup,drop,quantity,pickup_leg,drop_leg,travel_delta,added_duration,F,G,P,placements,quantity_evaluations,status\n"<<std::setprecision(17);
    auto record=[&](const Round73InsertionChoice& c,const char* status) {
        trace<<stats.accepted<<','<<processElapsedSeconds(opt)<<','<<c.vehicle<<','<<c.pickup<<','<<c.drop<<','<<c.quantity<<','
             <<c.pickup_leg<<','<<c.drop_leg<<','<<c.travel_delta<<','<<c.added_duration<<','<<verification.objective<<','
             <<verification.G<<','<<verification.P<<','<<stats.placements<<','<<stats.quantity_evaluations<<','<<status<<'\n';
        trace.flush();if(!trace)throw std::runtime_error("diagnostic trace failure");
    };
    record({},"initial_verified");
    for(;;) {
        auto c=bestRound73Insertion(in,routes,opt.lambda,stats,&opt);
        if(stats.deadline_reached){record({},"whole_run_deadline");break;}
        if(!c.found){stats.exhausted=true;record({},"motif_exhausted");break;}
        auto next=applyRound73Insertion(routes,c);auto checked=verifySolution(in,next,opt.lambda);
        if(!checked.feasible||!checked.errors.empty()||std::abs(checked.objective-c.objective)>1e-10||
            !(verification.objective-checked.objective>1e-12))throw std::runtime_error("diagnostic physical/objective disagreement");
        routes=std::move(next);verification=std::move(checked);++stats.accepted;
        if(stats.accepted>in.V)throw std::runtime_error("diagnostic finite-visit invariant failed");
        record(c,"accepted_verified");
    }
    snapshot("witness.json");
    std::ofstream result(out/"result.json");result<<std::setprecision(17)
        <<"{\"initial_F\":"<<initial<<",\"final_F\":"<<verification.objective
        <<",\"accepted\":"<<stats.accepted<<",\"passes\":"<<stats.passes
        <<",\"placements\":"<<stats.placements<<",\"quantity_evaluations\":"<<stats.quantity_evaluations
        <<",\"exhausted\":"<<(stats.exhausted?"true":"false")
        <<",\"deadline_reached\":"<<(stats.deadline_reached?"true":"false")
        <<",\"optimizer_calls\":0,\"scope\":\"fixed_witness_diagnosis_only\"}\n";
    result.flush();if(!result)throw std::runtime_error("diagnostic result write failure");
    return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
