#include "Round61Candidates.hpp"
#include "Evaluator.hpp"
#include "Round61TimeOracle.hpp"
#include "MipStartMapping.hpp"
#include <cmath>
#include <fstream>
#include <iostream>
#include <random>
#include <stdexcept>

namespace {
void require(bool ok,const char* msg) { if(!ok) throw std::runtime_error(msg); }
ebrp::Instance tiny() {
    ebrp::Instance in; in.V=2; in.M=2; in.Q={3,20};
    in.capacity={0,20,20}; in.initial={0,10,0}; in.target={0,20,20};
    in.weights={0,1,1}; in.min_ratio={0,0,0};
    in.dist={{0,1,1},{1,0,1},{1,1,0}};
    in.total_time_limit=100; in.pickup_time=1; in.drop_time=1;
    return in;
}
void incrementTests() {
    auto in=tiny();
    require(std::abs(ebrp::computeObjectiveParts(in,in.initial,.15).objective-.725)<1e-12,"initial F");
    require(std::abs(ebrp::computeObjectiveParts(in,{0,5,0},.15).objective-.7625)<1e-12,"worse intermediate F");
    require(std::abs(ebrp::computeObjectiveParts(in,{0,5,5},.15).objective-.225)<1e-12,"completed pair F");
    std::mt19937 rng(731);
    for(int trial=0;trial<400;++trial) {
        in.V=2+rng()%7; in.initial.resize(in.V+1); in.capacity.assign(in.V+1,30);
        in.target.resize(in.V+1); in.weights.resize(in.V+1);
        for(int i=1;i<=in.V;++i) {
            in.initial[i]=rng()%31; in.target[i]=1+rng()%25; in.weights[i]=(1+rng()%30)/17.0;
        }
        int a=1+rng()%in.V,b=1+rng()%in.V; if(a==b) b=0;
        const auto old=ebrp::computeObjectiveParts(in,in.initial,.27);
        for(int ya=0;ya<=30;++ya) for(int yb=0;yb<=30;++yb) {
            auto y=in.initial; y[a]=ya; if(b) y[b]=yb;
            auto inc=ebrp::round61Increment(in,in.initial,old,.27,a,ya-in.initial[a],b,b?yb-in.initial[b]:0);
            auto full=ebrp::computeObjectiveParts(in,y,.27);
            require(std::abs(inc.objective-full.objective)<2e-12,"increment and full objective mismatch");
        }
    }
    in=tiny(); in.initial={0,1,0};
    auto old=ebrp::computeObjectiveParts(in,in.initial,.15);
    require(std::abs(ebrp::round61Increment(in,in.initial,old,.15,1,-1,0,0).objective-.3)<1e-12,"S=0 convention");
}
void blockTests() {
    auto in=tiny();
    auto r=ebrp::constructRound61Block(in,.15);
    require(r.completed_blocks==1 && r.candidate.verified,"complete below-target block missing");
    require(std::abs(r.candidate.objective-.225)<1e-12,"must cross worse intermediate objective");
    require(r.candidate.routes[0].vehicle==1,"heterogeneous capacity selection");
    require(r.quantity_evaluations<=32*2048,"logical budget exceeded");
    auto repaired=ebrp::repairRound61Block(in,.15,r.candidate);
    require(repaired.candidate.objective<=r.candidate.objective+1e-12 &&
            ebrp::verifySolution(in,repaired.candidate.routes,.15).feasible,"repair monotonic feasibility");
    std::swap(in.initial[1],in.initial[2]);
    auto permuted=ebrp::constructRound61Block(in,.15);
    require(std::abs(permuted.candidate.objective-r.candidate.objective)<1e-12,"numbering bias under relabel");
    in=tiny(); in.initial={0,20,20}; in.target={0,10,10};
    r=ebrp::constructRound61Block(in,.15);
    require(r.accepted_singles>0 && r.trajectory.back().pickup>r.trajectory.back().drop,"loaded return eliminated");
    auto invalid=r.candidate.routes;
    invalid[0].nodes.insert(invalid[0].nodes.end()-1,invalid[0].nodes[1]);
    require(!ebrp::verifySolution(in,invalid,.15).feasible,"repeated service accepted");
    ebrp::Round61BlockOptions limit; limit.maximum_rounds=0;
    r=ebrp::constructRound61Block(in,.15,limit);
    require(r.candidate.routes.empty() && r.quantity_evaluations==0,"zero work must return legal input");
}
void prefixTests() {
    auto in=tiny();
    ebrp::HgaTgbcOptions options; options.fixed_generations=2; options.pop_size=4;
    options.iterations=1; options.max_time_seconds=20;
    auto off=ebrp::runHgaTgbcNative(in,options);
    options.publish_verified_improvements=true; options.retain_verified_on_log_failure=true;
    auto on=ebrp::runHgaTgbcNative(in,options);
    require(off.total_generations==2 && on.total_generations==2,"fixed logical prefix");
    require(off.fitness_history==on.fitness_history && off.decoder_calls==on.decoder_calls &&
        off.retained_candidate_sha256==on.retained_candidate_sha256,"observer changed logical/random trajectory");
    auto blocker=std::filesystem::temp_directory_path()/
        ("round61_log_"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
    { std::ofstream file(blocker); file<<"block"; }
    options.verified_candidate_log_path=blocker/"events.csv";
    options.generation_log_path=blocker/"generations.csv";
    auto failed=ebrp::runHgaTgbcNative(in,options);
    std::filesystem::remove(blocker);
    require(!failed.candidate_evidence_persisted && failed.found && failed.retained_verified_event_candidate,
            "telemetry failure lost independently verified memory");
    require(failed.retained_candidate_sha256==on.retained_candidate_sha256,"snapshot mismatch after log failure");
}
void oracleAndScopeTests() {
    auto in=tiny();
    require(std::abs(ebrp::round61SafeDurationBound(in)-23)<1e-12,"safe universal route duration");
    auto conflict=ebrp::round61InventoryNoGood(in,{0,5,-1});
    require(conflict.names.front()=="bit_1_0","actual canonical bit names");
    for(int inventory=0;inventory<=20;++inventory) {
        double activity=0;
        for(size_t h=0;h<conflict.coefficients.size();++h)
            activity+=conflict.coefficients[h]*((inventory>>h)&1);
        require((activity<conflict.rhs-.5)==(inventory==5),"no-good excludes precisely fixed pattern");
    }
    auto directory=std::filesystem::temp_directory_path()/
        ("round61_model_"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
    ebrp::Round61TimeRequest r; r.inventory={0,-1,5}; r.directory=directory;
    ebrp::writeRound61TimeModel(in,r);
    auto read=[&]() { std::ifstream f(directory/"time_oracle.lp"); return std::string(std::istreambuf_iterator<char>(f),{}); };
    auto first=read(); in.total_time_limit=.01; ebrp::writeRound61TimeModel(in,r);
    require(first==read(),"original T leaked into oracle domains or big-M");
    require(first.find("0 <= Y_1 <= 20")!=std::string::npos,"released supply station was deleted/fixed");
    std::filesystem::remove(directory/"time_oracle.lp"); std::filesystem::remove(directory);
    // A better global inventory outside a submodel cannot suppress another
    // applicable candidate: mapping is assessed per current model, independent
    // of the global store's better objective.
    in=tiny(); auto good=ebrp::constructRound61Block(in,.15).candidate;
    auto route_set=good.routes;
    ebrp::RoutePlan empty;empty.vehicle=0;empty.nodes={0,0};route_set.push_back(empty);
    auto normalized=ebrp::normalizeRound61Routes(in,.15,route_set);
    require(normalized.size()==1 && normalized.front().vehicle==1,
        "must remove empty placeholders without crossing unequal capacities");
    in.Q={20,20};
    normalized=ebrp::normalizeRound61Routes(in,.15,route_set);
    require(normalized.size()==1 && normalized.front().vehicle==0,
        "equal-Q used routes must precede unused vehicles");
    ebrp::VerifiedCandidateStore global; global.consider(in,.15,good.routes,"global","all");
    ebrp::SolveOptions options; ebrp::SolverNeutralModelDomain domain;
    domain.names={"G"}; domain.variable_types={'C'}; domain.lower_bounds={0};domain.upper_bounds={1};
    auto incompatible=ebrp::mapVerifiedRoutesToCanonicalModel(in,options,good.routes,"global",.1,.9,1,domain);
    require(!incompatible.complete,"global candidate should miss current G interval");
    auto compatible=ebrp::mapVerifiedRoutesToCanonicalModel(in,options,{},"empty",.1,.9,1,domain);
    require(compatible.complete,"model-applicable candidate incorrectly blocked by global best");
}
}
int main() { try { incrementTests(); blockTests(); prefixTests(); oracleAndScopeTests();
    std::cout<<"Round61 candidate mathematical and lifecycle tests passed\n"; return 0;
} catch(const std::exception& e) { std::cerr<<e.what()<<'\n'; return 1; } }
