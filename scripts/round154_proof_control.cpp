#include "Round154Research.hpp"
#include <iostream>
#include <cassert>
using namespace ebrp;
int main(){
    auto& c=round153();c.enabled=true;c.proof_only=true;c.accepted=true;
    c.gamma_L=0.;c.gamma_U=.8;c.cutoff=.7;c.lower=.6;round154().complete_root=true;
    ControllingLeafScheduler search;
    ControllingLeaf left;left.id="L0.0";left.gamma_L=0.;left.gamma_U=.4;left.cutoff=.7;
    left.lower_bound=.2;left.lower_bound_sources={"objective_nonnegative_penalty_G_floor"};
    ControllingLeaf right=left;right.id="L0.1";right.gamma_L=.4;right.gamma_U=.8;right.lower_bound=.5;
    assert(search.addLeaf(left)&&search.addLeaf(right));
    auto proof=round154ProofLedger(search);assert(proof.globalLowerBound()==.6);
    assert(search.globalLowerBound()==.2&&search.findLeaf(left.id)->lower_bound==.2);
    assert(search.findLeaf(left.id)->lower_bound_sources.size()==1);
    auto rejected=round154ProofLedger(search,false);assert(rejected.globalLowerBound()==.2);
    c.accepted=false;assert(round154ProofLedger(search).globalLowerBound()==.2);c.accepted=true;
    round154().complete_root=false;assert(round154ProofLedger(search).globalLowerBound()==.2);round154().complete_root=true;
    c.gamma_U=.4;assert(round154ProofLedger(search).globalLowerBound()==.5);c.gamma_U=.8;
    c.lower=.9;assert(round154ProofLedger(search).globalLowerBound()==.7); // cutoff complement
    std::string reason;assert(search.tightenVerifiedCutoff(.65,&reason));
    proof=round154ProofLedger(search);assert(proof.everyRelevantLeafClosed());
    assert(!search.everyRelevantLeafClosed());
    std::cout<<"{\"PASS\":true,\"fixtures\":7,\"uncovered_leaf_retains_raw\":true,\"search_unchanged\":true,\"cutoff_complement\":true,\"logical_proof_close\":true}\n";
}
