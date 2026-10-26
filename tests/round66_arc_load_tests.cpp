#include "CanonicalCompactModel.hpp"
#include "PaperK1AmSf.hpp"
#include "Round64SharedResource.hpp"
#include "Evaluator.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace {
void require(bool b, const char* s) { if (!b) throw std::runtime_error(s); }
std::string read(const std::filesystem::path& p) {
    std::ifstream f(p); return {(std::istreambuf_iterator<char>(f)), {}};
}
ebrp::Instance instance() {
    ebrp::Instance in;
    in.V=4; in.M=2; in.Q={2,4};
    in.initial={0,4,0,4,0}; in.capacity={0,8,8,8,8};
    in.target={0,2,2,2,2}; in.weights={0,.25,.25,.25,.25};
    in.min_ratio={0,0,0,0,0}; in.pickup_time=.3; in.drop_time=.7;
    in.total_time_limit=100;
    in.dist.assign(5,std::vector<double>(5,0));
    for(int i=0;i<=4;++i) for(int j=0;j<=4;++j)
        if(i!=j) in.dist[i][j]=(i*19+j*7)%17;
    return in;
}
void modelReplacement() {
    auto in=instance(); ebrp::SolveOptions opt;
    ebrp::configurePaperK1AmSfOverrides(opt);
    ebrp::CanonicalCompactModelSpec spec;
    spec.strengthened=true; spec.interval_restricted=true;
    spec.gamma_U=.75; spec.add_verified_incumbent_row=true;
    spec.verified_incumbent=10; spec.round51_subset_duration_big_m="off";
    const auto dir=std::filesystem::temp_directory_path()/"round66_arc_load_test";
    std::filesystem::create_directories(dir);
    const auto off=ebrp::writeCanonicalCompactModel(in,opt,dir/"off.lp",spec);
    require(off.written,"baseline model failed");
    opt.round64_shared_mode="q";
    const auto plus=ebrp::writeCanonicalCompactModel(in,opt,dir/"plus.lp",spec);
    require(plus.written,"Q-plus control failed");
    opt.round64_shared_mode="off"; opt.round66_arc_load_replacement=true;
    const auto repl=ebrp::writeCanonicalCompactModel(in,opt,dir/"replace.lp",spec);
    require(repl.written,"replacement model failed");
    require(plus.rows-repl.rows==2*in.M*in.V*in.V,"unexpected removed row count");
    require(plus.columns==repl.columns,"replacement changed Q column set");
    const auto text=read(repl.path), old=read(off.path);
    const auto gen=text.substr(text.find("Generals"),text.find("Binaries")-text.find("Generals"));
    require(gen.find("load_")==std::string::npos,"derived load remains integer");
    require(gen.find("p_0_1")!=std::string::npos,"pickup integrality lost");
    require(text.find("r64_q_balance_")!=std::string::npos,"load balance missing");
    require(text.find("r64q_0_1_0")!=std::string::npos,"loaded return removed");
    require(text.find("r64q_0_0_")==std::string::npos,"nonempty depot departure");
    require(text.find("conn_")!=std::string::npos,"connectivity removed");
    opt.round66_arc_load_replacement=false;
    const auto again=ebrp::writeCanonicalCompactModel(in,opt,dir/"again.lp",spec);
    require(again.written&&read(again.path)==old,"default off not byte preserving");
    opt.round66_arc_load_replacement=true; opt.plain_baseline=true;
    require(!ebrp::writeCanonicalCompactModel(in,opt,dir/"reject.lp",spec).written,
            "plain benchmark accepted replacement");
    opt.plain_baseline=false; opt.round65_budget=true;
    require(!ebrp::writeCanonicalCompactModel(in,opt,dir/"reject-budget.lp",spec).written,
            "resource-budget composition accepted");
    // Only remove our explicit single-test temporary directory.
    std::filesystem::remove_all(dir);
}
void fractionalImplication() {
    // Convex mixtures of physical routes give fractional x, q, p, d and L.
    // Check the omitted inactive-arc bounds as well as selected arcs.
    const auto in=instance();
    ebrp::RoutePlan a{0,{0,1,2,3,4,0},{{1,2,0},{2,0,2},{3,2,0},{4,0,1}}};
    ebrp::RoutePlan b{0,{0,3,2,1,4,0},{{3,1,0},{2,0,1},{1,2,0},{4,0,2}}};
    require(ebrp::verifySolution(in,{a},.15).feasible,"recycled loaded route invalid");
    require(ebrp::verifySolution(in,{b},.15).feasible,"second route invalid");
    for(int step=0;step<=20;++step) {
        double x[5][5]={},q[5][5]={},p[5]={},d[5]={},L[5]={};
        auto add=[&](const ebrp::RoutePlan& r,double w) {
            int load=0;
            for(std::size_t t=1;t<r.nodes.size();++t)x[r.nodes[t-1]][r.nodes[t]]+=w;
            for(std::size_t t=0;t<r.operations.size();++t) {
                const auto& op=r.operations[t]; load+=op.pickup-op.drop;
                const int i=r.nodes[t+1],j=r.nodes[t+2];
                q[i][j]+=w*load;p[i]+=w*op.pickup;d[i]+=w*op.drop;L[i]+=w*load;
            }
        };
        add(a,step/20.0);add(b,1-step/20.0);
        for(int i=1;i<=4;++i) {
            double incoming=0,outgoing=0;
            for(int j=0;j<=4;++j){incoming+=q[j][i];outgoing+=q[i][j];}
            require(std::abs(outgoing-L[i])<1e-12,"L projection mismatch");
            require(std::abs(outgoing-incoming-p[i]+d[i])<1e-12,"flow mismatch");
            require(std::abs(L[i]-p[i]+d[i])<=2*(1-x[0][i])+1e-12,"initial Big-M not implied");
            for(int j=1;j<=4;++j)if(i!=j)
                require(std::abs(L[j]-L[i]-p[j]+d[j])<=2*(1-x[i][j])+1e-12,
                        "inactive arc Big-M not implied");
        }
    }
}
}
int main() {
    try {modelReplacement();fractionalImplication();std::cout<<"Round66 arc replacement and fractional implications passed\n";return 0;}
    catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
