// Additional finite lifecycle qualification against the already-built core.
// No native library load or Optimize. Injected proof values are negative tests,
// never represented as solver evidence or used by a performance arm.
#include "Round119ProofContraction.hpp"
#include "FileSha256.hpp"
#include "Instance.hpp"
#include "Evaluator.hpp"
#include "Parser.hpp"
#include <algorithm>
#include <cmath>
#include <iostream>
#include <stdexcept>

using namespace ebrp;
static void check(bool v,const char* why){if(!v)throw std::runtime_error(why);}
static Round119Certificate proof(std::string parent,int depth,int side,double a,double b,double bound) {
    Round119Certificate p;p.parent=parent;p.leaf=parent+"."+std::to_string(side);
    p.depth=depth;p.side=side;p.call=2*depth+side+1;p.epoch=depth;
    p.model="finite_injected";p.path="finite_injected";p.scope="finite_injected";p.status="OPTIMAL";
    p.parent_lower=a;p.parent_upper=b;p.lower=side==0?a:(a+b)/2;p.upper=side==0?(a+b)/2:b;
    p.cutoff=.9;p.bound=bound;return p;
}
int main(int argc,char** argv){try {
    check(argc==3,"fixture and exclusive output directory required");
    const std::filesystem::path out(argv[2]);check(!std::filesystem::exists(out),"output already exists");
    std::filesystem::create_directories(out);
    ControllingLeaf root;root.id="L0";root.gamma_U=.8;root.cutoff=.9;
    ControllingLeafScheduler scheduler;std::string why;check(scheduler.addLeaf(root,&why),"root add");
    std::vector<Round119Certificate> proofs{proof("L0",0,0,0,.8,.1),proof("L0",0,1,0,.8,.6)};
    auto first=chooseRound119Contraction(proofs,root,{"L0"},.3,1e-7,8,1e-4);
    check(first.available && first.removed_side==1 && !first.close_both,"first strict contraction");
    ControllingLeaf left=root,right=root;left.id="L0.pc1.0";right.id="L0.pc1.1";
    left.parent_id=right.parent_id="L0";left.split_depth=right.split_depth=1;
    left.child_index=0;right.child_index=1;left.gamma_U=right.gamma_L=first.split;
    left.lower_bound=left.base_lower_bound=.1;right.lower_bound=right.base_lower_bound=.6;
    right.status=ControllingLeafStatus::Fathomed;
    check(scheduler.splitLeafAtomically("L0",{left,right},&why),"first atomic cover");
    proofs[first.proof].used=true;
    check(!chooseRound119Contraction(proofs,left,{"L0","L0.pc1.0"},.3,1e-7,8,1e-4).available,"same proof reuse");
    proofs.push_back(proof(left.id,1,0,0,.4,.1));proofs.push_back(proof(left.id,1,1,0,.4,.5));
    auto second=chooseRound119Contraction(proofs,left,{"L0",left.id},.3,1e-7,8,1e-4);
    check(second.available && second.split==.2 && second.proof!=first.proof,"second distinct strict contraction");
    ControllingLeaf ll=left,lr=left;ll.id="L0.pc2.0";lr.id="L0.pc2.1";
    ll.parent_id=lr.parent_id=left.id;ll.split_depth=lr.split_depth=2;ll.child_index=0;lr.child_index=1;
    ll.gamma_U=lr.gamma_L=second.split;lr.status=ControllingLeafStatus::Fathomed;
    lr.lower_bound=lr.base_lower_bound=.5;
    check(scheduler.splitLeafAtomically(left.id,{ll,lr},&why),"second atomic cover");
    check(scheduler.findLeaf(ll.id)->split_depth==2 && scheduler.findLeaf("L0")->parent_replaced,"depth and lineage inherited");
    proofs[second.proof].used=true;
    auto exhausted=ll;exhausted.split_depth=8;
    check(!chooseRound119Contraction(proofs,exhausted,{"L0",left.id,ll.id},.3,1e-7,8,1e-4).available,"depth limit");
    exhausted.split_depth=2;exhausted.gamma_U=1e-4;
    check(!chooseRound119Contraction(proofs,exhausted,{"L0",left.id,ll.id},.3,1e-7,8,1e-4).available,"width finite");
    // An already sufficient original cover is resolved by the old controller.
    auto closed=root;closed.lower_bound=.3;
    check(!chooseRound119Contraction(proofs,closed,{"L0"},.3,1e-7,8,1e-4).available,"closed cover rebuilt");
    auto both=std::vector<Round119Certificate>{proof("L0",0,0,0,.8,.5),proof("L0",0,1,0,.8,.6)};
    check(chooseRound119Contraction(both,root,{"L0"},.3,1e-7,8,1e-4).close_both,"both halves closure");
    // A physical incumbent, its repeated callbacks, and a deliberately false
    // same-scope numerical claim exercise revocation without any solver call.
    auto in=parseInstanceFile(argv[1],1000,60,60);SolveOptions opt;opt.lambda=.15;
    RoutePlan pickup;pickup.vehicle=0;pickup.nodes={0,1,0};pickup.operations.push_back({1,1,0});
    std::vector<RoutePlan> routes{pickup};
    const auto v=verifySolution(in,routes,.15);check(v.feasible && std::fabs(v.objective-.3)<1e-12,"physical loaded-return witness");
    Round119ProofContraction archive(in,opt,out/"physical_negative_events.jsonl",routes,1e-7);
    archive.observe(routes,10);archive.observe(routes,11);
    check(std::fabs(archive.upper()-.3)<1e-12,"repeated callback changed U");
    auto false_claim=proof("L0",0,0,0,1,.4);
    const auto artifact=out/"injected_not_a_solver_model.txt";{std::ofstream f(artifact);f<<"negative finite proof injection only\n";}
    false_claim.path=artifact.string();false_claim.model=fileSha256(artifact);
    bool rejected=false;try{archive.add(false_claim);}catch(const std::exception&){rejected=true;}
    check(rejected && archive.failed() && !archive.choose(root,{"L0"}).available,"same-scope contradiction did not revoke");
    check(std::fabs(archive.upper()-.3)<1e-12,"revocation lost physical own U");
    std::ofstream report(out/"lifecycle.json");report<<"{\"passed\":true,\"Optimize\":0,\"two_distinct_atomic_contractions\":true,\"depth_inherited\":true,\"finite_depth_and_width\":true,\"same_proof_not_reused\":true,\"complete_cover_without_rebuild\":true,\"both_halves_close\":true,\"physical_repeat_callbacks\":true,\"physical_counterexample_revokes\":true,\"injected_proof_not_native_evidence\":true}\n";
    std::cout<<"finite lifecycle qualification passed; Optimize=0\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
