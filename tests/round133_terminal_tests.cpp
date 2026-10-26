#include "PaperExternalGiniTree.hpp"
#include "FixedIntervalMipBackend.hpp"
#include <iostream>
#include <stdexcept>
using namespace ebrp;
int main() {try {
    FixedIntervalMipOutcome out;
    out.attempted=out.available=out.solver_finalization_reached=true;
    out.model_fingerprint_matches_request=out.exact_zero_gap_roundtrip=true;
    out.feasibility_consistency_gate=out.terminal_mip=out.optimal=true;
    out.native_bound_available=out.incumbent_independently_verified=true;
    out.native_bound=.31538869722423574;out.incumbent_objective=.31538912105343897;
    auto open=evaluatePaperTerminalMipDecision(out);
    if(!open.valid||!open.leave_open_and_stop||open.close_leaf||
       open.reason!="native_optimal_physical_gap_open")throw std::runtime_error("GEOM physical gap must stay open");
    out.incumbent_objective=out.native_bound;
    auto normal=evaluatePaperTerminalMipDecision(out);
    if(!normal.valid||!normal.close_leaf)throw std::runtime_error("normal qualified optimum still closes");
    out.available=false;
    if(evaluatePaperTerminalMipDecision(out).close_leaf)throw std::runtime_error("unqualified source cannot close");
    out.available=true;out.optimal=false;out.infeasible=true;
    if(!evaluatePaperTerminalMipDecision(out).close_leaf)throw std::runtime_error("qualified infeasibility remains supported");
    out.terminal_mip=false;out.partial_bound_target_mip=true;out.optimal=true;out.infeasible=false;
    out.incumbent_objective=out.native_bound+4.2e-7;
    if(!nativeOptimalPhysicalGapOpen(out))throw std::runtime_error("same gap rule applies to target returns");
    const auto next=evaluateC6FrontierDecision(.1,{.3},1e-7);
    NativeEvidenceScope scope;scope.native_preconditions=true;scope.gmax=.5;
    scope.upper_g=.5;scope.cutoff=.2;scope.model_sha256=std::string(64,'a');
    const auto floor=evaluateNativeLocalBound(scope,.4,{});
    if(!next.valid||!next.run_native_target||!floor.available||
       !(floor.value+1e-7<next.native_bound_target))
        throw std::runtime_error("NEXT must compare unconditional floor, not restricted raw bound");
    ControllingLeafScheduler scheduler;
    ControllingLeaf parent;parent.id="parent";parent.gamma_U=.5;parent.cutoff=.65;parent.lower_bound=.1;
    if(!scheduler.addLeaf(parent))throw std::runtime_error("parent fixture invalid");
    ControllingLeaf left=parent,right=parent;
    left.id="left";left.gamma_U=.25;left.lower_bound=.2;
    right.id="right";right.gamma_L=.25;right.base_lower_bound=.25;right.lower_bound=.3;
    left.parent_id=right.parent_id="parent";left.split_depth=right.split_depth=1;
    left.child_index=0;right.child_index=1;left.base_lower_bound=.1;
    auto broken=left;broken.gamma_U=.2;
    if(scheduler.splitLeafAtomically("parent",{broken,right}))
        throw std::runtime_error("incomplete child cover cannot replace parent");
    if(!scheduler.splitLeafAtomically("parent",{left,right})||scheduler.globalLowerBound()!=.2)
        throw std::runtime_error("complete child cover retains qualified disjunction floor");
    if(!scheduler.tightenVerifiedCutoff(.25)||!scheduler.abandonNativeSources(.5,.25)||
       scheduler.globalLowerBound()!=0||scheduler.leaves().size()!=1||
       scheduler.leaves()[0].status!=ControllingLeafStatus::Open)
        throw std::runtime_error("no child max/closure survives revocation after cutoff epoch change");
    std::cout<<"terminal, target, source rejection and normal proof checks pass; zero Optimize\n";
    return 0;
}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
