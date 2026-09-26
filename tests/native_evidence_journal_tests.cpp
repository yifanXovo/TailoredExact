#include "NativeEvidenceJournal.hpp"
#include "Evaluator.hpp"
#include <chrono>
#include <cmath>
#include <fstream>
#include <iostream>
#include <stdexcept>
using namespace ebrp;
namespace {
int checks=0;
void require(bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);}
Instance fixture() {
    Instance in;in.V=2;in.M=1;in.Q={2};in.initial={0,2,0};in.target={0,1,1};
    in.capacity={0,2,2};in.weights={0,.5,.5};in.dist.assign(3,std::vector<double>(3,0));
    in.total_time_limit=10;in.pickup_time=in.drop_time=1;return in;
}
void write(const std::filesystem::path& p,const std::string& x){std::ofstream f(p,std::ios::binary);f<<x;}
}
int main(){try{
    auto in=fixture();std::vector<RoutePlan> empty={{0,{0,0},{}}};
    const auto v=verifySolution(in,empty,.15);
    require(v.feasible && std::fabs(v.objective-.65)<1e-12,"independent physical fixture");
    NativeEvidenceScope s;s.full_original=true;s.native_preconditions=true;s.gmax=.5;
    s.model_sha256=std::string(64,'a');
    auto d=evaluateNativeEvidenceBound(s,.2,{v});
    require(d.available&&d.value==.2,"full original native scope");
    require(evaluateNativeEvidenceBound(s,.7,{v}).inconsistent,"global numerical contradiction");
    s.native_preconditions=false;
    require(!evaluateNativeEvidenceBound(s,.2,{v}).available,"failed precondition rejects native promotion");
    s.full_original=false;s.native_preconditions=true;s.cutoff=.65;s.lower_g=0;s.upper_g=.3;s.leaf="a";
    s.cover={{"a","tested_lp",0,.3,.1,.65},{"b","tested_lp",.3,.5,.35,.65}};
    d=evaluateNativeEvidenceBound(s,.25,{v});
    require(d.available&&d.value==.25,"complete cover strengthens only matching active leaf");
    s.leaf="probe";
    require(!evaluateNativeEvidenceBound(s,.6,{v}).available,"prospective child is not a live parent replacement");
    s.leaf="a";s.upper_g=.2;
    require(!evaluateNativeEvidenceBound(s,.25,{v}).available,"same id different range rejected");
    s.upper_g=.3;s.cover[1].lower_g=.30000000001;
    require(!evaluateNativeEvidenceBound(s,.25,{v}).available,"tiny real coverage gap is not hidden by tolerance");
    s.cover[1].lower_g=.3;s.cover[1].upper_g=.4;
    require(!evaluateNativeEvidenceBound(s,.25,{v}).available,"uncovered physical G tail");
    s.cover[1].upper_g=.5;s.leaf="b";s.lower_g=.3;s.upper_g=.5;
    require(evaluateNativeEvidenceBound(s,.7,{v}).inconsistent,"reject local contradiction before cutoff minimum");
    s.cover[1].cutoff=.5;
    require(!evaluateNativeEvidenceBound(s,.4,{v}).available,"foreign stronger cutoff cannot cover current domain");
    s.cover[1].cutoff=.65;s.cutoff=.4;
    require(!evaluateNativeEvidenceBound(s,.4,{v}).available,"unwitnessed cutoff is not an upper bound");
    s.cutoff=.65;s.leaf="a";s.lower_g=0;s.upper_g=.3;
    s.cover={{"a","scope",0,.3,.1,.65}};
    require(!evaluateNativeEvidenceBound(s,.25,{v}).available,"local interval alone never global");
    auto better=verifySolution(in,{{0,{0,1,2,0},{{1,1,0},{2,0,1}}}},.15);
    require(better.feasible && better.objective==0,"independent lower witness");
    s.cutoff=.3;s.cover={{"a","scope",0,.3,0,.3}};
    d=evaluateNativeEvidenceBound(s,0,{better});
    require(d.available&&d.value==0,"omitted G tail explicitly bounded by objective cutoff");

    ControllingLeaf parent;parent.id="p";parent.gamma_U=.5;parent.cutoff=.65;
    parent.parent_replaced=true;parent.status=ControllingLeafStatus::Replaced;
    parent.single_child_contraction_parent=true;parent.strict_infeasible_half_verified=true;
    parent.contracted_infeasible_gamma_U=.3;parent.contraction_source="strict_complete_midpoint_child_lp_infeasible";
    ControllingLeaf child;child.id="b";child.gamma_L=.3;child.gamma_U=.5;child.lower_bound=.35;child.cutoff=.65;
    s.cover=nativeEvidenceCover({parent,child});s.cutoff=.65;s.leaf="b";s.lower_g=.3;s.upper_g=.5;
    d=evaluateNativeEvidenceBound(s,.4,{v});
    require(d.available&&d.value==.4,"verified contraction half restores complete cover");
    parent.strict_infeasible_half_verified=false;s.cover=nativeEvidenceCover({parent,child});
    require(!evaluateNativeEvidenceBound(s,.4,{v}).available,"unproved deleted half does not count as coverage");

    const auto root=std::filesystem::current_path()/("native_evidence_test_"+
        std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
    require(std::filesystem::create_directory(root),"owned unique test directory");
    in.path=(root/"input.txt").string();write(in.path,"physical fixture identity\n");
    SolveOptions opt;opt.process_start_time_valid=true;opt.process_start_time=std::chrono::steady_clock::now();
    opt.lambda=.15;opt.native_evidence_dir=(root/"journal").string();
    NativeEvidenceJournal journal(in,opt);
    NativeEvidenceScope full;full.full_original=full.native_preconditions=true;full.gmax=.5;
    const auto call=journal.beginCall(full);journal.witness(empty,"verified_fixture");journal.nativeBound(call,.2);
    std::string payload,why;const auto receipt=root/"journal/event_4.commit";
    require(readNativeEvidenceReceipt(receipt,1,2,payload,why)&&payload.find("\"global_bound\":0.2")!=std::string::npos,
        "callback-time data readable before normal return");
    require(!readNativeEvidenceReceipt(receipt,3,2,payload,why),"post-cutoff observation cannot be backdated");
    std::filesystem::create_directory(root/"partial");
    write(root/"partial/event_4.commit","NEJ1 4 0.1 20 deadbeef");
    require(!readNativeEvidenceReceipt(root/"partial/event_4.commit",1,2,payload,why),"partial receipt rejected");
    require(!readNativeEvidenceReceipt(root/"partial/event_9.commit",1,2,payload,why),"missing receipt rejected");
    std::filesystem::create_directory(root/"corrupt");
    std::filesystem::copy_file(receipt,root/"corrupt/event_4.commit");
    write(root/"corrupt/event_4.json","corrupt\n");
    require(!readNativeEvidenceReceipt(root/"corrupt/event_4.commit",1,2,payload,why),"corrupt immutable content rejected");
    bool duplicate=false;try{NativeEvidenceJournal again(in,opt);}catch(...){duplicate=true;}
    require(duplicate,"journal cannot overwrite an earlier run");
    journal.witness(empty,"native_MIPSOL_verified_original_routes",call);
    require(readNativeEvidenceReceipt(root/"journal/event_5.commit",1,2,payload,why)&&
        payload.find("\"improving\":0")!=std::string::npos,"first non-improving native witness is persisted");
    journal.witness({{0,{0,1,2,0},{{1,1,0},{2,0,1}}}},"new_better_physical_witness");
    require(!journal.enabled(),"later witness also rejects previously stored contradictory bound");
    require(readNativeEvidenceReceipt(root/"journal/event_6.commit",1,2,payload,why)&&
        payload.find("new_better_physical_witness")!=std::string::npos,"contradicting physical evidence retained");
    require(readNativeEvidenceReceipt(root/"journal/event_7.commit",1,2,payload,why)&&
        payload.find("\"kind\":\"failure\"")!=std::string::npos,"inconsistency evidence retained");
    std::cout << checks << " scope, coverage, physical contradiction and receipt checks passed; zero Optimize calls\n";
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
