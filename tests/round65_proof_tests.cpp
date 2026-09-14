#include "Round65Proof.hpp"
#include "HgaTgbcRunner.hpp"
#include "Evaluator.hpp"
#include "PaperK1AmSf.hpp"
#include "Round65Projection.hpp"
#include "Round64SharedResource.hpp"
#include "ControllingLeafScheduler.hpp"
#include <filesystem>
#include <iostream>
#include <stdexcept>
using namespace ebrp;
void require(bool b, const char* why) { if (!b) throw std::runtime_error(why); }
void projectionTests() {
    Instance in; in.V=4;in.M=2;in.Q={2,4};in.initial={0,5,5,5,5};in.capacity={0,10,10,10,10};
    in.target={0,5,5,5,5};in.weights={0,.25,.25,.25,.25};in.pickup_time=.3;in.drop_time=.7;in.total_time_limit=100;
    in.dist.assign(5,std::vector<double>(5,1));for(int i=0;i<=4;++i)in.dist[i][i]=0;
    std::vector<RoutePlan> routes={{0,{0,1,2,3,4,0},{{1,2,0},{2,0,2},{3,2,0},{4,0,1}}}};
    const auto resource=round64RouteResourceValues(in,routes);
    for(bool zero:{false,true}){
        if(zero)in.pickup_time=in.drop_time=0;
        auto data=prepareRound63Time(in);const auto qf=round64RouteResourceValues(in,routes);
        std::set<std::string> all_names;
        for(int k=0;k<2;++k){
            auto m=makeRound65VehicleMatrix(in,data,k);
            require(m.names.size()==32 && m.vehicle==k,"per vehicle size");
            std::map<std::string,double> v;
            for(auto [n,u]:m.original_upper){(void)u;v[n]=0;}
            std::vector<double> z;
            for(const auto& n:m.names){require(all_names.insert(n).second,"vehicle columns independent");
                const auto it=qf.find((n[0]=='q'?"r64q_":"r63f_")+n.substr(2));
                z.push_back(it==qf.end()?0:it->second);}
            if(k==0){int load=0;for(std::size_t t=0;t+1<routes[0].nodes.size();++t){
                int i=routes[0].nodes[t],j=routes[0].nodes[t+1];v["x_0_"+std::to_string(i)+"_"+std::to_string(j)]=1;
                if(i){auto op=routes[0].operations[t-1];load+=op.pickup-op.drop;v["p_0_"+std::to_string(i)]=op.pickup;
                    v["d_0_"+std::to_string(i)]=op.drop;v["load_0_"+std::to_string(i)]=load;}}}
            for(const auto& r:m.rows){long double a=0,b=0;for(auto [j,c]:r.auxiliary)a+=c*z[j];for(auto [n,c]:r.rhs)b+=c*v.at(n);
                require((r.equality?std::abs(a-b):a-b)<1e-10,"integer embedding in every vehicle block");}
            std::vector<double> ray(m.rows.size(),0);ray[0]=-1; // negative <= multiplier is clamped then recomputed
            require(!verifyRound65Combination(m,ray,v).valid,"invalid ray cannot exclude a feasible route");
            ray[0]=std::numeric_limits<double>::quiet_NaN();require(!verifyRound65Combination(m,ray,v).valid,"nonfinite multiplier rejected");
        }
    }
    // Column residual -1 on z in [0,3] contributes -3. Ignoring this term
    // would incorrectly cut a valid completion at v=-2.
    Round65VehicleMatrix m;m.identity="unit";m.vehicle=0;m.names={"z"};m.upper={3};m.original_upper={{"v",10}};
    m.rows={{"r",false,{{0,-1}},{{"v",1}}}};
    require(!verifyRound65Combination(m,{1},{{"v",0}}).valid,"negative residual compensated");
    auto row=verifyRound65Combination(m,{1},{{"v",-4}});
    require(row.valid && row.rhs<=-3 && row.rhs>-3.0000001 && row.violation>.99,"finite bound correction and raw violation");
    m.upper[0]=std::numeric_limits<double>::infinity();require(!verifyRound65Combination(m,{1},{{"v",-4}}).valid,"no fabricated finite bound");
    ControllingLeafScheduler s;ControllingLeaf parent;parent.id="p";parent.gamma_L=0;parent.gamma_U=1;parent.cutoff=2;parent.lower_bound=.1;parent.base_lower_bound=.1;
    require(s.addLeaf(parent),"parent");auto left=parent,right=parent;left.id="l";left.parent_id="p";left.gamma_U=.5;
    right.id="r";right.parent_id="p";right.gamma_L=.5;
    left.child_index=0;right.child_index=1;left.split_depth=right.split_depth=1;
    require(!s.splitLeafAtomically("p",{left}) && !s.findLeaf("p")->parent_replaced,"incomplete transaction retains parent");
    require(s.splitLeafAtomically("p",{left,right}),"complete coverage commits");
    require(s.setStatus("l",ControllingLeafStatus::Empty,"proved LP empty"),"empty child recorded");
    require(std::abs(s.globalLowerBound()-.1)<1e-12,"unknown survivor keeps inherited bound");
}
int main() { try {
    projectionTests();
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
