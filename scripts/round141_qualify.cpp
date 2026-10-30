// Finite new-risk qualification: no Native library or Optimize here.
#include "Round141Research.hpp"
#include "Round127Research.hpp"
#include "Round138Research.hpp"
#include "PaperK1AmSf.hpp"
#include "NativeEvidenceJournal.hpp"
#include "MipStartMapping.hpp"
#include "Evaluator.hpp"
#include <iostream>
using namespace ebrp;
int main(int argc,char** argv){try {
    if(argc!=2)throw std::runtime_error("qualification output required");
    const std::filesystem::path dir(argv[1]);std::filesystem::create_directories(dir);
    int checks=0;auto check=[&](bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);};
    Instance in;in.V=2;in.M=1;in.Q={2};in.initial={0,2,0};in.target={0,1,1};in.capacity={0,2,2};
    in.weights={0,.5,.5};in.dist.assign(3,std::vector<double>(3,0));in.total_time_limit=10;in.pickup_time=in.drop_time=1;
    in.path=(dir/"fixture.txt").string();{std::ofstream f(in.path);f<<"two-station physical fixture identity\n";}
    SolveOptions opt;configurePaperK1AmSfOverrides(opt);opt.round98_state_service="m-binary";opt.lambda=.15;
    round127().mode="ms2";round138().stock_rlt=true;round140().set("tc2");round137Apply(opt,"ms2");
    CanonicalCompactModelSpec spec;spec.strengthened=spec.interval_restricted=spec.add_verified_incumbent_row=true;
    spec.gamma_L=0;spec.gamma_U=.5;spec.verified_incumbent=.7;spec.station_state_formulation="vd-p";spec.round51_subset_duration_big_m="off";
    auto base=writeCanonicalCompactModel(in,opt,dir/"parent.lp",spec);check(base.written,"tiny canonical writer");
    auto& state=round141();state.mode="d1";state.ready=true;state.root_artifact=base;auto& c=state.choice;
    c.ratios={0,1,1};c.support=round141_detail::supports(round141_detail::material(base.path),2);c.exponent=-52;
    c.threshold=round140_detail::units(1.,c.exponent);c.ell=0;c.u=2;c.pivot=1;c.a=0;c.z=.5;c.cutoff=.7;c.model_cutoff=.7;
    c.root_sha=base.sha256;c.support_sha=std::string(64,'c');c.input_sha=fileSha256(in.path);c.beta={{.1,0}};
    auto low=verifySolution(in,{{0,{0,0},{}}},.15);
    auto high=verifySolution(in,{{0,{0,1,2,0},{{1,1,0},{2,0,1}}}},.15);
    check(low.feasible&&high.feasible&&round141Count(c,low.final_inventory)==1&&round141Count(c,high.final_inventory)==2,"two independently verified physical sides");
    SolverNeutralModelDomain domain;domain.names={"r141_b"};domain.lower_bounds={0};domain.upper_bounds={1};domain.variable_types={'B'};
    auto start0=mapVerifiedRoutesToCanonicalModel(in,opt,{{0,{0,0},{}}},"tiny_low",0,.5,.7,domain);
    auto start1=mapVerifiedRoutesToCanonicalModel(in,opt,{{0,{0,1,2,0},{{1,1,0},{2,0,1}}}},"tiny_high",0,.5,.7,domain);
    check(start0.complete&&start1.complete&&start0.values==std::vector<double>{0}&&start1.values==std::vector<double>{1},"actual Start mapper uses physical Y on both sides");
    NativeEvidenceScope scope;scope.native_preconditions=true;scope.model_sha256=base.sha256;scope.leaf="count_low";scope.gmax=.5;
    scope.lower_g=0;scope.upper_g=.5;scope.cutoff=.7;scope.settings_json="{\"round141_count_scope\":\""+round141ScopePayload(c,0)+"\"}";
    check(evaluateNativeLocalBound(scope,.1,{high}).available,"other-side lower witness is not a contradiction");
    check(evaluateNativeLocalBound(scope,.7,{low}).inconsistent,"same-side lower witness refutes raw bound");
    check(!evaluateNativeLocalInfeasibility(scope,{high}).inconsistent,"other-side feasible witness does not refute side infeasibility");
    check(evaluateNativeLocalInfeasibility(scope,{low}).inconsistent,"same-side witness refutes side infeasibility");
    check(!evaluateNativeEvidenceBound(scope,.1,{high}).available,"count side never becomes global Gini coverage");
    auto malformed=scope;malformed.settings_json="{\"round141_count_scope\":\"bad\"}";
    check(!evaluateNativeLocalScope(malformed).available,"malformed count scope fails closed");
    opt.process_start_time_valid=true;opt.process_start_time=std::chrono::steady_clock::now();opt.native_evidence_dir=(dir/"revocation_journal").string();
    NativeEvidenceJournal journal(in,opt);scope.leaf="count_high";scope.settings_json="{\"round141_count_scope\":\""+round141ScopePayload(c,1)+"\"}";
    auto call=journal.beginCall(scope);journal.nativeBound(call,.1);journal.witness({{0,{0,0},{}}},"opposite_side");check(journal.proofUsable(),"opposite side does not revoke");
    journal.witness({{0,{0,1,2,0},{{1,1,0},{2,0,1}}}},"same_side_counterexample");check(!journal.proofUsable(),"same-side counterexample revokes source and dependents");
    round141Probe(in,0,dir/"count_low.lp");round141Probe(in,1,dir/"count_high.lp");
    round141Embed(base,.7,dir/"d1.lp");state.mode="d0";round141Embed(base,.7,dir/"d0.lp");
    auto successor_spec=spec;successor_spec.gamma_U=.25;successor_spec.verified_incumbent=.65;
    auto successor=writeCanonicalCompactModel(in,opt,dir/"successor.lp",successor_spec);
    check(round141Contains(c,successor,.65),"containing successor domain admitted");
    round141Embed(successor,.65,dir/"successor_d0.lp");
    check(!round141Contains(c,base,.71),"cutoff expansion rejected");
    auto expanded=base;expanded.gamma_U=.6;check(!round141Contains(c,expanded,.7),"Gini expansion rejected");
    std::ofstream f(dir/"tiny.json");f<<std::setprecision(17)<<"{\"PASS\":true,\"checks\":"<<checks<<",\"Optimize\":0,\"offset_cases\":[";
    bool first=true;for(double a:{.1,.4})for(double b:{.1,.4})for(double constant:{-.25,.25}) {
        Round120Pair p;p.a=0;p.m=1;p.b=2;p.beta0=a;p.beta1=b;auto r=round120Rows(p,true,constant);
        check(round120Endpoints(r,p,true),"directed offset endpoints");
        if(!first)f<<',';first=false;f<<"{\"beta0\":"<<a<<",\"beta1\":"<<b<<",\"ObjCon\":"<<constant
            <<",\"base\":"<<r.objective_base<<",\"delta\":"<<r.objective_delta<<'}';
    }f<<"],\"physical_start_b\":[0,1],\"proof_revocation\":true,\"scope\":\"new count-domain, writer and Start risks only\"}\n";f.close();check(bool(f),"tiny report");
    std::cout<<"PASS "<<checks<<" count proof checks; Optimize=0\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
