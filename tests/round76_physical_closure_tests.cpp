#include "Round76PhysicalClosure.hpp"
#include "Evaluator.hpp"
#include "Round60Candidates.hpp"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <fstream>
#include <iostream>
#include <set>
#include <sstream>
#include <stdexcept>

using namespace ebrp;
static void require(bool ok,const char* reason) {if(!ok)throw std::runtime_error(reason);}
static Instance fixture() {
    Instance in;in.V=4;in.M=1;in.Q={4};
    in.initial={0,4,0,4,0};in.capacity.assign(5,4);
    in.target.assign(5,2);in.weights.assign(5,.25);in.weights[0]=0;
    in.pickup_time=0;in.drop_time=0;in.total_time_limit=100;
    in.dist.assign(5,std::vector<double>(5,1));
    for(int i=0;i<=4;++i)in.dist[i][i]=0;
    return in;
}
static std::vector<std::string> fields(const std::string& line) {
    std::vector<std::string> out;std::istringstream input(line);std::string value;
    while(std::getline(input,value,','))out.push_back(value);
    return out;
}
// Replay the composition trace independently of both production materializers.
// The proposal APIs have separate exhaustive structural oracles in R73/R75.
static void replay(const Instance& in,const SolveOptions& options,
    const std::vector<RoutePlan>& input,const Round76ClosureResult& result,
    const std::filesystem::path& path) {
    auto routes=input;auto previous=verifySolution(in,routes,options.lambda);
    std::set<std::vector<int>> inventories;inventories.insert(previous.final_inventory);
    std::ifstream stream(path);std::string line;std::getline(stream,line);
    std::uint64_t accepted=0;double prior_time=-1;std::string terminal;
    while(std::getline(stream,line)) {
        const auto row=fields(line);require(row.size()==21,"complete trace row");
        const auto elapsed=std::stod(row[1]);require(elapsed>=prior_time,"trace times monotone");prior_time=elapsed;
        terminal=row[20];if(terminal!="accepted_verified")continue;
        if(row[2]=="insertion") {
            const int k=std::stoi(row[3]),p=std::stoi(row[4]),d=std::stoi(row[5]);
            const int q=std::stoi(row[6]),a=std::stoi(row[7]),b=std::stoi(row[8]);
            require(q>0 && (p || d),"nonzero insertion");
            for(const auto& r:routes)for(const auto& op:r.operations)
                require(op.station!=p && op.station!=d,"insertion uses unvisited stations");
            auto found=std::find_if(routes.begin(),routes.end(),[&](const RoutePlan& r){return r.vehicle==k;});
            if(found==routes.end()) {routes.push_back({k,{0,0},{}});found=routes.end()-1;}
            if(d) {found->nodes.insert(found->nodes.begin()+b+1,d);found->operations.push_back({d,0,q});}
            if(p) {found->nodes.insert(found->nodes.begin()+a+1,p);found->operations.push_back({p,q,0});}
        } else {
            require(row[2]=="quantity","recognized proposal type");
            const int a=std::stoi(row[11]),b=std::stoi(row[12]),t=std::stoi(row[13]);
            require(a>0 && a!=b && t!=0,"nonzero quantity change");int found=0;
            for(auto& r:routes) {
                for(auto& op:r.operations)if(op.station==a || (b && op.station==b)) {
                    ++found;const int s=op.pickup-op.drop+(op.station==a?t:-t);
                    op.pickup=std::max(0,s);op.drop=std::max(0,-s);
                    if(!s)r.nodes.erase(std::find(r.nodes.begin(),r.nodes.end(),op.station));
                }
                r.operations.erase(std::remove_if(r.operations.begin(),r.operations.end(),
                    [](const StopOperation& op){return !op.pickup && !op.drop;}),r.operations.end());
            }
            require(found==(b?2:1),"quantity change uses current served nodes");
        }
        ++accepted;require(std::stoull(row[0])==accepted,"contiguous accepted steps");
        const auto v=verifySolution(in,routes,options.lambda);
        require(v.feasible && v.errors.empty() && v.original_objective_recomputed,"replayed physical original witness");
        require(previous.objective-v.objective>1e-12,"every adopted step strictly improves original F");
        require(std::abs(v.objective-std::stod(row[14]))<1e-10 &&
            std::abs(v.G-std::stod(row[15]))<1e-10 && std::abs(v.P-std::stod(row[16]))<1e-10,
            "trace F/G/P match original formula");
        require(inventories.insert(v.final_inventory).second,"finite inventory state never repeats");previous=v;
    }
    require(terminal=="joint_neighborhood_exhausted","honest joint exhaustion");
    require(accepted==result.stats.accepted && canonicalCandidateSerialization(routes)==
        canonicalCandidateSerialization(result.routes),"independent replay matches returned route");
    Round73InsertionStats i;Round75QuantityStats q;
    require(!bestRound73Insertion(in,routes,options.lambda,i).found &&
        !bestRound75QuantityChange(in,routes,options.lambda,q).found,"both endpoint neighborhoods exhausted");
    require(std::filesystem::exists(path.string()+".initial.json") &&
        std::filesystem::exists(path.string()+".final.json"),"physical snapshots retained");
}
int main() {
    try {
        auto in=fixture();SolveOptions options;options.lambda=1;
        std::vector<RoutePlan> seed={{0,{0,1,2,0},{{1,1,0},{2,0,1}}}};
        const auto root=std::filesystem::current_path()/("round76_structural_"+
            std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
        require(!std::filesystem::exists(root),"fresh evidence directory");
        const auto trace=root/"closure.csv";
        const auto result=runRound76PhysicalClosure(in,options,seed,trace);
        require(result.stats.exhausted && !result.stats.verification_failed && !result.stats.deadline_reached,
            "normal closure terminates without a numerical or resource rejection");
        require(result.stats.accepted_insertions>0 && result.stats.accepted_quantities>0,
            "same descent genuinely composes insertion with quantity correction");
        require(std::abs(result.verification.objective)<1e-12,"symmetric balanced synthetic fixture reaches F zero");
        replay(in,options,seed,result,trace);
        const auto again=runRound76PhysicalClosure(in,options,seed);
        require(canonicalCandidateSerialization(again.routes)==canonicalCandidateSerialization(result.routes),
            "deterministic proposal and tie ordering");
        // Fresh empty support and already-exhausted support both remain valid.
        const auto empty=runRound76PhysicalClosure(in,options,{},root/"empty.csv");
        replay(in,options,{},empty,root/"empty.csv");
        const auto fixed=runRound76PhysicalClosure(in,options,result.routes,root/"fixed.csv");
        replay(in,options,result.routes,fixed,root/"fixed.csv");
        require(!fixed.stats.accepted && fixed.stats.exhausted,"fixed point performs no artificial step");
        auto expired=options;expired.process_start_time_valid=true;
        expired.process_start_time=std::chrono::steady_clock::now()-std::chrono::seconds(5);
        expired.process_wall_time_limit=1;expired.process_shutdown_margin_seconds=0;
        const auto stopped=runRound76PhysicalClosure(in,expired,seed,root/"deadline.csv");
        require(stopped.stats.deadline_reached && !stopped.stats.exhausted && !stopped.stats.accepted &&
            canonicalCandidateSerialization(stopped.routes)==canonicalCandidateSerialization(seed),
            "whole deadline preserves witness without false exhaustion");
        auto invalid=seed;invalid[0].operations[0].pickup=5;bool refused=false;
        try {runRound76PhysicalClosure(in,options,invalid);}catch(const std::exception&){refused=true;}
        require(refused,"physically invalid original input is rejected");
        std::cout<<"Round76 composition: insertion="<<result.stats.accepted_insertions
            <<", quantity="<<result.stats.accepted_quantities<<", replayed="
            <<result.stats.accepted+empty.stats.accepted<<", joint_exhaustion=3, evidence="<<root<<'\n';
    } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
