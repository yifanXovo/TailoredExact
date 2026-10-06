#include "Round105Decomposition.hpp"
#include "Evaluator.hpp"
#include "PaperK1AmSf.hpp"
#include "PhysicalWitnessValidation.hpp"
#include "ProcessPhaseLedger.hpp"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <fstream>
#include <iostream>
#include <numeric>
#include <stdexcept>

using namespace ebrp;
static void require(bool b,const char* message){if(!b)throw std::runtime_error(message);}
static Instance fixture(const std::vector<int>& q,int Q,double T,int M=1) {
    Instance in;in.V=static_cast<int>(q.size());in.M=M;in.Q.assign(M,Q);
    in.capacity.assign(in.V+1,Q+5);in.initial.assign(in.V+1,0);in.target.assign(in.V+1,1);
    in.weights.assign(in.V+1,1);in.initial[0]=in.capacity[0]=in.target[0]=0;
    for(int i=1;i<=in.V;++i)in.initial[i]=std::max(0,q[i-1]);
    in.total_time_limit=T;in.pickup_time=in.drop_time=1;
    in.dist.assign(in.V+1,std::vector<double>(in.V+1,0));
    for(int i=0;i<=in.V;++i)for(int j=0;j<=in.V;++j)if(i!=j)in.dist[i][j]=i && j ? 2 : 1;
    return in;
}
// Independent exhaustive order implementation: no production writer/verifier.
static bool enumerate(const Instance& in,const Round105Pattern& p) {
    std::vector<int> order;for(int i=1;i<=in.V;++i)if(p.operation[i])order.push_back(i);
    if(order.empty())return true;
    do {
        int load=0,pick=0,last=0;double t=0;bool valid=true;
        for(int i:order){load+=p.operation[i];pick+=std::max(0,p.operation[i]);
            if(load<0 || load>in.Q[p.vehicle])valid=false;t+=in.dist[last][i];last=i;}
        t+=in.dist[last][0]+(in.pickup_time+in.drop_time)*pick;
        if(valid && t<=in.total_time_limit+1e-7)return true;
    }while(std::next_permutation(order.begin(),order.end()));return false;
}
static double conflictValue(const Round105Conflict& cut,const Instance& in,const Round105Pattern& candidate,
                            const std::vector<int>& global_inventory) {
    double value=0;
    for(const auto& [n,c]:cut.coefficients) {
        if(n.rfind("z_",0)==0) {const auto j=n.find('_',2);int station=std::stoi(n.substr(j+1));value+=c*(candidate.operation[station]!=0);}
        else {const auto j=n.find('_',6);int station=std::stoi(n.substr(6,j-6));int y=std::stoi(n.substr(j+1));value+=c*(global_inventory[station]==y);}
    }
    (void)in;return value;
}
int main(int argc,char** argv) {
    try {
        const bool native=argc==3 && std::string(argv[1])=="native";
        const std::filesystem::path dir=native ? argv[2] : "round105_test_artifacts";
        auto b=fixture({2,2,-3,-1},3,100);
        Round105Pattern bad{0,{0,2,2,-3,0}},good{0,{0,2,2,-3,-1}};
        require(!enumerate(b,bad),"B bad has route");require(enumerate(b,good),"B repair absent");
        const auto full=round105Conflict(b,bad,{1,2,3,4});
        auto inventory=b.initial;for(int i=1;i<=4;++i)inventory[i]-=bad.operation[i];
        require(conflictValue(full,b,bad,inventory)>full.rhs,"full cut fails to remove current");
        inventory[4]-=good.operation[4];
        require(conflictValue(full,b,good,inventory)<=full.rhs,"full cut removes helper repair");
        const auto naive=round105Conflict(b,bad,{1,2,3});
        require(conflictValue(naive,b,good,inventory)>naive.rhs,"naive counterexample not reproduced");
        // Same inventory can be assigned to another vehicle: local row must allow it.
        auto other=bad;std::fill(other.operation.begin(),other.operation.end(),0);
        require(conflictValue(full,b,other,inventory)<=full.rhs,"local cut fixed global Y");
        auto invalid=bad;invalid.operation[1]=4;bool rejected=false;
        try{round105ValidatePattern(b,invalid);}catch(...){rejected=true;}require(rejected,"invalid Q accepted");
        auto a=fixture({4,-1,-1,-1,-1},4,16,2);a.initial[1]=5;a.target[1]=1;
        Round105Pattern pa{0,{0,4,-1,-1,-1,-1}};
        require(!enumerate(a,pa),"A incorrectly feasible at T16");a.total_time_limit=18;require(enumerate(a,pa),"A not feasible at T18");
        auto qlarge=b;qlarge.Q[0]=4;require(enumerate(qlarge,bad),"different Q ignored");
        auto key=round105PatternKey(b,bad);require(key!=round105PatternKey(qlarge,bad),"cache ignores Q");
        auto tdiff=b;tdiff.total_time_limit=8;require(key!=round105PatternKey(tdiff,bad),"cache ignores T");
        auto dchange=b;dchange.dist[1][2]+=0.25;require(key!=round105PatternKey(dchange,bad),"cache ignores travel");
        auto returning=fixture({3,-1},3,10);Round105Pattern pr{0,{0,3,-1}};
        require(enumerate(returning,pr),"loaded return rejected");
        auto repeated=fixture({2,-2,2,-2},3,16);Round105Pattern pp{0,{0,2,-2,2,-2}};
        require(enumerate(repeated,pp),"cumulative pickup above Q rejected");
        if(native) {
            std::filesystem::create_directories(dir);
            std::ofstream out(dir/"qualification.csv");out<<"case,enumeration,native_status,core_confirmed,groups\n";
            int id=0;
            auto test=[&](const Instance& in,const Round105Pattern& p,bool core) {
                SolveOptions opt;opt.process_start_time=std::chrono::steady_clock::now();opt.process_start_time_valid=true;
                opt.process_wall_time_limit=120;opt.process_shutdown_margin_seconds=0;opt.lambda=0.15;opt.gurobi_home="D:/gurobi1302/win64";
                const auto r=solveRound105OracleDiagnostic(in,opt,p,dir/("case_"+std::to_string(++id)),core);
                const bool truth=enumerate(in,p);out<<id<<','<<truth<<','<<static_cast<int>(r.status)<<','<<r.core_confirmed<<','<<r.core.size()<<'\n';out.flush();
                require(r.status==(truth ? Round105OracleStatus::Feasible : Round105OracleStatus::ProvedInfeasible),"native/enumeration disagreement");
            };
            test(b,bad,true);test(b,good,true);test(qlarge,bad,false);test(returning,pr,false);test(repeated,pp,false);
            a.total_time_limit=16;test(a,pa,true);a.total_time_limit=18;test(a,pa,false);
            test(b,Round105Pattern{0,{0,0,0,0,0}},false);
            test(b,Round105Pattern{0,{0,0,0,-3,0}},true);
            // Exact boundary, and empty/negative operating modes.
            for(int v=0;v<12;++v) {
                auto in=fixture({2,2,-3,-1},3,8+v);
                Round105Pattern p{0,{0,(v&1)?2:1,(v&2)?2:0,(v&4)?-3:-1,(v&8)?-1:0}};
                test(in,p,v==3 || v==7);
            }
            // Exercise the actual master/conflict/UB-LB loop on B's instance.
            SolveOptions opt;configurePaperK1AmSfOverrides(opt);opt.round105_decomposition="core";
            opt.gurobi_home="D:/gurobi1302/win64";opt.external_gini_artifact_dir=(dir/"loop").string();
            opt.process_start_time=std::chrono::steady_clock::now();opt.process_start_time_valid=true;
            opt.process_wall_time_limit=120;opt.process_shutdown_margin_seconds=0;
            auto loop_in=b;loop_in.initial={0,3,3,0,1};loop_in.target={0,1,1,3,1};
            SolveResult seed;seed.routes={{0,{0,0},{}}};seed.verification=verifyCompletePhysicalStartingWitness(loop_in,seed.routes,opt.lambda);
            seed.upper_bound=seed.objective=seed.verification.objective;seed.final_inventory=loop_in.initial;
            const auto result=solveRound105Decomposition(loop_in,opt,seed);
            require(result.strict_certified_original_problem,"tiny exact loop did not certify");
            require(result.lower_bound<=result.upper_bound+1e-7,"tiny loop bound inversion");
            std::ifstream summary(dir/"loop/round105/summary.json");std::string content((std::istreambuf_iterator<char>(summary)),{});
            require(content.find("\"conflicts\":0,")==std::string::npos,"tiny loop did not learn a conflict");
            out<<"loop,1,"<<result.status<<",0,0\n";
        }
        std::cout<<"Round105 independent counterexamples and contracts PASS"<<(native ? "; native PASS" : "")<<'\n';
    } catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}return 0;
}
