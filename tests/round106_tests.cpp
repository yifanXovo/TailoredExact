#include "Round106Events.hpp"
#include "Round106Research.hpp"
#include "Parser.hpp"
#include "Evaluator.hpp"
#include "PaperK1AmSf.hpp"
#include "PhysicalWitnessValidation.hpp"
#include "ProcessPhaseLedger.hpp"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iostream>
#include <stdexcept>

using namespace ebrp;
static void require(bool b,const char* why){if(!b)throw std::runtime_error(why);}
static Instance square() {
    Instance in;in.V=4;in.M=1;in.Q={3};in.capacity={0,5,5,5,5};in.initial={0,2,0,1,1};
    in.target={0,1,3,1,1};in.weights={0,1,1,1,1};in.pickup_time=in.drop_time=1;in.total_time_limit=20;
    in.points={{0,0},{3,0},{3,3},{0,3},{3,2}};in.dist.assign(5,std::vector<double>(5));
    for(int i=0;i<5;++i)for(int j=0;j<5;++j)in.dist[i][j]=std::hypot(in.points[i].first-in.points[j].first,in.points[i].second-in.points[j].second);
    return in;
}
static double shortestLegal(const Instance& in,const Round105Pattern& p) {
    std::vector<int> order;for(int i=1;i<=in.V;++i)if(p.operation[i])order.push_back(i);
    double best=1e100;
    do{int load=0,pick=0,last=0;double t=0;bool valid=true;
        for(int s:order){load+=p.operation[s];pick+=std::max(0,p.operation[s]);
            if(load<0||load>in.Q[p.vehicle])valid=false;t+=in.dist[last][s];last=s;}
        t+=in.dist[last][0]+(in.pickup_time+in.drop_time)*pick;
        if(valid)best=std::min(best,t);
    }while(std::next_permutation(order.begin(),order.end()));return best;
}
static SolveOptions options(const std::filesystem::path& dir,const std::string& strategy,double cap=120) {
    SolveOptions o;configurePaperK1AmSfOverrides(o);o.round106_events=strategy;o.gurobi_home="D:/gurobi1302/win64";
    o.external_gini_artifact_dir=dir.string();o.process_start_time=std::chrono::steady_clock::now();
    o.process_start_time_valid=true;o.process_wall_time_limit=cap;o.process_shutdown_margin_seconds=0;return o;
}
static SolveResult emptySeed(const Instance& in,const SolveOptions& o) {
    SolveResult s;for(int k=0;k<in.M;++k)s.routes.push_back({k,{0,0},{}});
    s.verification=verifyCompletePhysicalStartingWitness(in,s.routes,o.lambda);
    require(s.verification.feasible,"empty physical seed");s.objective=s.upper_bound=s.verification.objective;
    s.final_inventory=s.verification.final_inventory;return s;
}
int main(int argc,char** argv) {
    try {
        const bool native=argc==3&&std::string(argv[1])=="native";
        const auto dir=argc==3?std::filesystem::path(argv[2]):std::filesystem::path("round106_test_artifacts");
        std::filesystem::create_directories(dir);
        auto in=square();Round105Pattern bad{0,{0,2,-3,1,0}},helper{0,{0,2,-3,1,1}};
        require(std::abs(shortestLegal(in,bad)-(12+6*std::sqrt(2.0)))<1e-9,"balanced no-helper duration");
        require(std::abs(shortestLegal(in,helper)-20)<1e-9,"balanced helper not legal at boundary");
        const auto travel=round106ConservativeTravel(in);
        auto boundary=round106Separate(in,bad,travel);
        require(std::none_of(boundary.begin(),boundary.end(),[](const auto& c){return c.family.rfind("B_",0)==0;}),"equal-budget helper unsafely excluded");
        require(verifyCompletePhysicalStartingWitness(in,{{0,{0,1,4,2,3,0},{{1,2,0},{4,1,0},{2,0,3},{3,1,0}}}},.15).feasible,"helper loaded return physical");
        auto f2=parseInstanceFile("reference/round86_unadapted_confirmation/F2.txt",3600,60,60);
        Round105Pattern fp{0,std::vector<int>(f2.V+1)};fp.operation[6]=9;fp.operation[7]=-16;fp.operation[9]=7;
        auto fc=round106Separate(f2,fp,round106ConservativeTravel(f2));int bc=0;
        for(const auto& c:fc)if(c.family.rfind("B_",0)==0){++bc;require(c.orders.size()==6&&c.pickup==16&&c.delivery==16,"F2 balanced proof");
            require(c.travel_lower>1661.12&&c.travel_lower<1661.136&&c.budget_margin>100,"F2 automatic strong lower bound");round106WriteCertificate(dir/(c.family+".json"),c);}
        require(bc==2,"F2 automatic exact and threshold conflict missing");
        auto c2=parseInstanceFile("reference/round98_confirmation/C2.txt",7200,60,60);
        Round105Pattern cp{0,std::vector<int>(c2.V+1)};const int ids[]={1,5,6,13,17,21},q[]={8,6,6,7,9,7};
        for(int j=0;j<6;++j)cp.operation[ids[j]]=q[j];
        auto cc=round106Separate(c2,cp,round106ConservativeTravel(c2));
        auto a=std::find_if(cc.begin(),cc.end(),[](const auto& c){return c.family=="A_MST";});
        require(a!=cc.end()&&a->support==std::vector<int>({1,5,6,13,17,21})&&a->pickup==43&&a->row.coefficients.size()==12,"C2 sparse dynamic A");
        require(a->travel_lower>2387.25&&a->travel_lower<2387.255&&a->budget_margin>347,"C2 conservative MST");round106WriteCertificate(dir/"C2_A.json",*a);
        auto zero=in;zero.initial.assign(5,0);const auto parts=computeObjectiveParts(zero,zero.initial,.15);require(parts.G==0&&std::isfinite(parts.objective),"zero denominator original objective");
        if(native) {
            // The inherited nonmonotone helper fixture forces actual native fallback/lazy.
            auto loop=in;loop.V=4;loop.initial={0,3,3,0,1};loop.target={0,1,1,3,1};loop.total_time_limit=100;
            for(int i=0;i<=4;++i)for(int j=0;j<=4;++j)loop.dist[i][j]=i==j?0:(i&&j?2:1);
            for(const std::string strategy:{"full","core","struct"}) {
                auto o=options(dir/strategy,strategy);const auto seed=emptySeed(loop,o);
                const auto result=solveRound106Events(loop,o,seed);
                require(result.status!="error"&&result.strict_certified_original_problem,"single-tree native loop not certified");
                require(std::abs(result.upper_bound-0.11818181818181819)<1e-7,"helper loop optimum mismatch");
                std::ifstream s(dir/strategy/"round106/summary.json");std::string text((std::istreambuf_iterator<char>(s)),{});
                require(text.find("\"master_calls\":1")!=std::string::npos,"outer master actively restarted");
                require(text.find("\"lazy_calls\":0,")==std::string::npos,"no actual lazy exercised");
            }
            auto contract=options(dir/"contracts","full");
            round106AdapterContracts(loop,contract,dir/"full/round106/master_0.lp",
                dir/"full/round106/candidate_2.sol",dir/"full/round106/submission_1.sol",
                dir/"full/round106/start.mst");
            auto trip=in;trip.initial={0,3,0,2,1};trip.target={0,1,3,1,1};trip.total_time_limit=19.99;
            auto bo=options(dir/"native_B","struct");const auto br=solveRound106Events(trip,bo,emptySeed(trip,bo));
            require(br.status!="error"&&br.strict_certified_original_problem,"native B fixture correctness");
            auto a=in;a.Q={30};a.initial={0,2,2,2,0};a.target={0,1,1,1,3};a.total_time_limit=15;
            a.points={{0,0},{10,0},{10,0},{10,0},{0,0}};
            for(int i=0;i<=4;++i)for(int j=0;j<=4;++j)a.dist[i][j]=std::hypot(a.points[i].first-a.points[j].first,a.points[i].second-a.points[j].second);
            auto ao=options(dir/"native_A","struct");const auto ar=solveRound106Events(a,ao,emptySeed(a,ao));
            require(ar.status!="error"&&ar.strict_certified_original_problem,"native A fixture correctness");
            auto expired=options(dir/"expired","struct",.001);expired.process_start_time-=std::chrono::seconds(1);
            const auto seed=emptySeed(in,expired);const auto r=solveRound106Events(in,expired,seed);
            require(r.status!="error"&&!r.strict_certified_original_problem&&r.lower_bound==0&&std::abs(r.upper_bound-seed.upper_bound)<1e-7,"pre-expired bounds/UNKNOWN");
        }
        std::cout<<"Round106 independent order/anchor/boundary contracts PASS"<<(native?"; native PASS":"")<<'\n';
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}return 0;
}
