#include "Round107Scope.hpp"
#include "CanonicalCompactModel.hpp"
#include "PaperExternalGiniTree.hpp"
#include "PaperK1AmSf.hpp"
#include "PhysicalWitnessValidation.hpp"
#include "FileSha256.hpp"
#include "ProcessPhaseLedger.hpp"
#include "Parser.hpp"
#include "Round107Research.hpp"
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
using namespace ebrp;
static void need(bool b,const char* s){if(!b)throw std::runtime_error(s);}
static Instance loop() {
    Instance a;a.V=4;a.M=1;a.Q={3};a.capacity={0,5,5,5,5};a.initial={0,3,3,0,1};
    a.target={0,1,1,3,1};a.weights={0,1,1,1,1};a.pickup_time=a.drop_time=1;a.total_time_limit=100;
    a.dist.assign(5,std::vector<double>(5));for(int i=0;i<=4;++i)for(int j=0;j<=4;++j)a.dist[i][j]=i==j?0:(i&&j?2:1);
    a.name="qualification_loop";return a;
}
static SolveOptions options(const std::filesystem::path& d,double cap=120) {
    SolveOptions o;configurePaperK1AmSfOverrides(o);o.round107_frontier_struct=true;
    o.external_gini_interval_mip_policy="round55-vd-p";o.external_gini_artifact_dir=d.string();
    o.gurobi_home="D:/gurobi1302/win64";o.log_path=(d/"native.log").string();
    o.process_wall_time_limit=cap;o.process_shutdown_margin_seconds=0;
    o.process_start_time=std::chrono::steady_clock::now();o.process_start_time_valid=true;return o;
}
static SolveResult seed(const Instance& a,const SolveOptions& o) {
    SolveResult s;for(int k=0;k<a.M;++k)s.routes.push_back({k,{0,0},{}});s.verification=verifyCompletePhysicalStartingWitness(a,s.routes,o.lambda);
    s.objective=s.upper_bound=s.verification.objective;s.G=s.verification.G;s.P=s.verification.P;s.final_inventory=s.verification.final_inventory;
    s.frontier_covers_all_improving_gini_values=true;
    return s;
}
static FixedIntervalMipRequest request(const Instance& a,const SolveOptions& o,const SolveResult& s,
    const std::filesystem::path& d,double lo,double hi,double eps=0) {
    CanonicalCompactModelSpec spec;spec.strengthened=spec.interval_restricted=spec.add_verified_incumbent_row=true;
    spec.gamma_L=lo;spec.gamma_U=hi;spec.verified_incumbent=s.upper_bound;spec.incumbent_epsilon=eps;
    spec.station_state_formulation="vd-p";spec.round51_subset_duration_big_m="off";
    const auto m=writeCanonicalCompactModel(a,o,d/"canonical.lp",spec);need(m.written,"fixture canonical");
    FixedIntervalMipRequest q;q.solve_kind=FixedIntervalSolveKind::PaperTerminalMip;q.leaf_id="fixture";
    q.gamma_L=lo;q.gamma_U=hi;q.verified_cutoff=s.upper_bound;q.global_deadline_remaining_seconds=120;
    q.canonical_model_path=m.path;q.canonical_model_fingerprint=m.sha256;q.canonical_row_signature=m.row_signature;
    q.canonical_model_scope=m.model_scope;q.verified_start_routes=s.routes;return q;
}
static void instanceEvidence(const Instance& a,const SolveOptions& o,const std::filesystem::path& file) {
    std::filesystem::create_directories(file.parent_path());
    std::ofstream f(file);f<<std::setprecision(17)<<"{\"V\":"<<a.V<<",\"M\":"<<a.M<<",\"T\":"<<a.total_time_limit
        <<",\"pickup_seconds\":"<<a.pickup_time<<",\"drop_seconds\":"<<a.drop_time<<",\"lambda\":"<<o.lambda;
    auto vector=[&](const char* key,const auto& v){f<<",\""<<key<<"\":[";for(std::size_t j=0;j<v.size();++j){if(j)f<<',';f<<v[j];}f<<']';};
    vector("Q",a.Q);vector("capacity",a.capacity);vector("initial",a.initial);vector("target",a.target);vector("weights",a.weights);
    f<<",\"dist\":[";for(std::size_t i=0;i<a.dist.size();++i){if(i)f<<',';f<<'[';for(std::size_t j=0;j<a.dist[i].size();++j){if(j)f<<',';f<<a.dist[i][j];}f<<']';}f<<"]}\n";f.flush();need(bool(f),"instance evidence persist");
}
static void controllerEvidence(const SolveResult& tree,const std::filesystem::path& file) {
    std::ofstream f(file);f<<std::setprecision(17)<<std::boolalpha<<"{\"certified\":"<<tree.strict_certified_original_problem
        <<",\"UB\":"<<tree.upper_bound<<",\"LB\":"<<tree.lower_bound<<",\"partial_calls\":"<<tree.external_gini_tree_partial_mip_optimize_count
        <<",\"target_reached\":"<<(tree.external_gini_tree_next_leaf_target_reached_count+tree.external_gini_tree_child_bound_target_reached_count)
        <<",\"requeues\":"<<tree.external_gini_tree_native_requeue_count<<",\"terminal_calls\":"<<tree.external_gini_tree_terminal_mip_optimize_count
        <<",\"status\":"<<std::quoted(tree.status)<<",\"failure\":"<<std::quoted(tree.external_gini_tree_failure_reason)
        <<",\"actual_Optimize_count\":"<<tree.external_gini_tree_optimize_count<<",\"deadline_count\":"<<tree.external_gini_tree_global_deadline_interruption_count<<"}\n";
}
int main(int argc,char** argv) {
    try {
        const auto dir=argc>=3?std::filesystem::path(argv[2]):std::filesystem::path("round107_pure");
        std::filesystem::create_directories(dir);
        Round107ScopeFacts f;f.own_global_ub=.2;f.native_infeasible=true;
        need(decideRound107Scope(f).empty_improvement_domain,"local INF without Start");
        f.domain_witness_embeds=true;need(!decideRound107Scope(f).valid,"INF contradicts in-domain embedding");
        f={};f.own_global_ub=.2;f.native_optimal=true;f.bound_available=true;f.bound=.3;f.final_mode_verified=true;
        need(decideRound107Scope(f).close_by_dominance,"local LB above global UB legitimate");
        f.bound=.1;need(!decideRound107Scope(f).close_by_dominance&&decideRound107Scope(f).stop_whole_run,"native OPTIMAL not automatic closure");
        f.native_optimal=false;f.target_requested=f.target_observed=true;f.target=.09;
        need(decideRound107Scope(f).target_reached,"local target qualified");
        f.unresolved=true;need(!decideRound107Scope(f).target_reached&&decideRound107Scope(f).stop_whole_run,"UNKNOWN precedes target");
        f.error=true;need(!decideRound107Scope(f).valid,"numeric/API error loses eligibility");
        ControllingLeafScheduler scheduler(1e-7);ControllingLeaf low,high;
        low.id="low";low.gamma_L=0;low.gamma_U=.1;low.cutoff=.2;low.lower_bound=0;
        high.id="high";high.gamma_L=.1;high.gamma_U=.2;high.cutoff=.2;high.lower_bound=.3;
        std::string why;need(scheduler.addLeaf(low,&why)&&scheduler.addLeaf(high,&why),"coverage fixture leaves");
        need(scheduler.globalLowerBound()==0,"high leaf cannot close low obligation");
        if(argc>=2&&std::string(argv[1])=="target") {
            // Finite qualification domains, fixed before native results. No performance handoff.
            std::ofstream table(dir/"finite_fixture_domains.csv");table<<"case,parent_LB,left_LB,right_LB,AM_score,AM_decision,actual_target,requeues,terminal\n";
            bool qualified=false;
            for(int c=0;c<8&&!qualified;++c) {
                auto a=loop();a.target={0,1,2,3,4};a.M=2;a.Q={3,4};
                a.weights={0,1,1,1,static_cast<double>(2+c*2)};
                a.initial={0,1,2,2,1};
                const auto d=dir/("case_"+std::to_string(c));auto o=options(d,180);const auto s=seed(a,o);
                instanceEvidence(a,o,d/"instance.json");const double hi=std::min(.75,s.upper_bound);
                auto b=makeGurobiFixedIntervalBackend(a,o);std::vector<PaperLpResult> lps;
                for(int part=0;part<3;++part){const double lo=part==2?hi/2:0,up=part==1?hi/2:hi;
                    auto q=request(a,o,s,d/("lp_"+std::to_string(part)),lo,up);q.solve_kind=FixedIntervalSolveKind::PaperLpRelaxation;
                    const auto x=b->solve(q);need(x.lp_terminal_valid&&x.feasibility_consistency_gate,"finite actual LP fixture");
                    PaperLpResult l;l.terminal_valid=x.lp_terminal_valid;l.optimal=x.optimal;l.infeasible=x.infeasible;
                    l.bound_available=x.native_bound_available;l.lower_bound=x.native_bound;lps.push_back(l);
                }b->release();
                const auto am=evaluateC6AdaptiveMassSplitDecision(lps[0].lower_bound,s.upper_bound,lps[1],lps[2],o.split_threshold,1e-7,false);
                SolveResult tree;
                if(am.run_child_bound_target||am.split_immediately) {auto tree_o=options(d/"controller",180);tree=solvePaperExternalGiniTree(a,tree_o,s,0,hi);controllerEvidence(tree,d/"controller_result.json");
                    qualified=tree.external_gini_tree_native_requeue_count>0&&tree.external_gini_tree_partial_mip_optimize_count>0&&
                        (tree.external_gini_tree_terminal_mip_optimize_count>0||tree.external_gini_tree_split_count>0)&&
                        (tree.external_gini_tree_next_leaf_target_reached_count+tree.external_gini_tree_child_bound_target_reached_count)>0;
                }
                table<<std::setprecision(17)<<c<<','<<lps[0].lower_bound<<','<<lps[1].lower_bound<<','<<lps[2].lower_bound<<','<<am.adaptive_mass_score<<','<<am.reason<<','
                    <<(tree.external_gini_tree_next_leaf_target_reached_count+tree.external_gini_tree_child_bound_target_reached_count)<<','<<tree.external_gini_tree_native_requeue_count<<','<<tree.external_gini_tree_terminal_mip_optimize_count<<'\n';table.flush();
            }
            need(qualified,"actual native mathematical target/controller qualification not exposed");
        }
        if(argc>=2&&std::string(argv[1])=="deadline") {
            auto a=parseInstanceFile("reference/round98_confirmation/C2.txt",7200,60,60);auto o=options(dir,15);auto s=seed(a,o);
            instanceEvidence(a,o,dir/"instance.json");auto q=request(a,o,s,dir,0,static_cast<double>(a.V-1)/a.V);
            auto b=makeGurobiFixedIntervalBackend(a,o);const auto out=b->solve(q);b->release();
            need(out.interrupted&&out.round107_open_stop&&!out.optimal&&!out.infeasible,"actual deadline scoped open stop");
            std::ofstream f(dir/"deadline_outcome.json");const auto counts=b->stats();f<<std::boolalpha<<std::setprecision(17)<<"{\"failure\":"<<std::quoted(out.failure_reason)
                <<",\"reason\":"<<std::quoted(out.round107_local_reason)<<",\"actual_master_Optimize\":"<<counts.optimize_count
                <<",\"unresolved\":"<<out.round107_unresolved_stop<<",\"certified\":false,\"target_reached\":"<<out.native_bound_target_reached
                <<",\"LB\":"<<out.native_bound<<",\"UB\":"<<out.incumbent_objective<<"}\n";
            need(counts.optimize_count>0,"deadline requires actual Optimize");
        }
        if(argc>=2&&std::string(argv[1])=="inner-deadline") {
            Instance a;a.V=60;a.M=1;a.Q={3};a.total_time_limit=850;a.pickup_time=a.drop_time=1;
            a.capacity.assign(a.V+1,5);a.initial.assign(a.V+1,2);a.target.assign(a.V+1,2);a.weights.assign(a.V+1,1);
            a.dist.assign(a.V+1,std::vector<double>(a.V+1));std::vector<std::pair<double,double>> points(a.V+1);
            for(int i=1;i<=a.V;++i)points[i]={((i*7919)%104729)/1000.,((i*15401+51)%104729)/1000.};
            for(int i=0;i<=a.V;++i)for(int j=0;j<=a.V;++j)a.dist[i][j]=std::hypot(points[i].first-points[j].first,points[i].second-points[j].second);
            auto o=options(dir,3.0);instanceEvidence(a,o,dir/"instance.json");Round105Pattern p;p.vehicle=0;p.operation.assign(a.V+1,0);
            for(int i=1;i<=a.V;++i)p.operation[i]=i%2?1:-1;
            const auto answer=round107OracleDeadlineQualification(a,o,p,dir/"inner");
            need(answer.status==Round105OracleStatus::Unknown,"genuine inner native deadline UNKNOWN");
            std::ofstream f(dir/"pattern.json");f<<"{\"operation\":[";for(int i=0;i<=a.V;++i){if(i)f<<',';f<<p.operation[i];}f<<"],\"UNKNOWN_cached_as_INF\":false}\n";
        }
        if(argc>=2&&std::string(argv[1])=="native") {
            auto a=loop();auto o=options(dir/"terminal");auto s=seed(a,o);auto q=request(a,o,s,dir/"terminal",0,std::min(1.,s.upper_bound));
            auto b=makeGurobiFixedIntervalBackend(a,o);const auto out=b->solve(q);
            need(out.feasibility_consistency_gate&&out.optimal&&out.native_bound_available&&out.incumbent_independently_verified,"native scoped terminal closure");
            need(std::abs(out.incumbent_objective-.11818181818181819)<1e-7,"physical optimum");
            auto strict_o=options(dir/"strict");s=seed(a,strict_o);s.routes=out.incumbent_routes;
            s.verification=verifyCompletePhysicalStartingWitness(a,s.routes,strict_o.lambda);s.upper_bound=s.verification.objective;
            auto strict=request(a,strict_o,s,dir/"strict",0,.75,1e-4);
            const auto inf=b->solve(strict);need(inf.infeasible&&!inf.warm_start_mapping_complete&&inf.feasibility_consistency_gate,"strict empty domain without Start");
            auto outside_o=options(dir/"outside");s=seed(a,outside_o);q=request(a,outside_o,s,dir/"outside",.6,.7);
            const auto outside=b->solve(q);
            need(outside.feasibility_consistency_gate&&!outside.warm_start_mapping_complete,"global witness outside leaf not physical error");b->release();
            auto tree_o=options(dir/"controller");s=seed(a,tree_o);
            const auto tree=solvePaperExternalGiniTree(a,tree_o,s,0,std::min(s.upper_bound,.75));
            std::cout<<"controller status="<<tree.status<<" failure="<<tree.external_gini_tree_failure_reason<<'\n';
            need(tree.external_gini_tree_failure_reason=="none"||tree.external_gini_tree_failure_reason.empty(),"native controller scope gate");
            std::ofstream f(dir/"native_controller_result.json");f<<std::boolalpha<<"{\"certified\":"<<tree.strict_certified_original_problem
                <<",\"UB\":"<<tree.upper_bound<<",\"LB\":"<<tree.lower_bound<<",\"partial_calls\":"<<tree.external_gini_tree_partial_mip_optimize_count
                <<",\"target_reached\":"<<(tree.external_gini_tree_next_leaf_target_reached_count+tree.external_gini_tree_child_bound_target_reached_count)<<",\"requeues\":"<<tree.external_gini_tree_native_requeue_count
                <<",\"terminal_calls\":"<<tree.external_gini_tree_terminal_mip_optimize_count<<"}\n";
        }
        std::cout<<"Round107 scoped contracts PASS\n";
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
