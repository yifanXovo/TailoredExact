#pragma once
#include "Round153Research.hpp"
#include "ControllingLeafScheduler.hpp"

namespace ebrp {
struct Round154ProofControls {
    bool complete_root=false,stopped=false;
};
inline Round154ProofControls& round154(){static Round154ProofControls c;return c;}
inline void round154ResetRun(){round154()=Round154ProofControls{};}
inline bool round154Enabled(){return round153().enabled&&round153().proof_only;}

// The existing scheduler/ledger is copied only for proof composition. The
// original scheduler, native bounds, AM parent/child inputs and order survive.
inline ControllingLeafScheduler round154ProofLedger(
    const ControllingLeafScheduler& search,bool sources_live=true) {
    auto proof=search;const auto& c=round153();
    if(!round154Enabled()||!c.accepted||!round154().complete_root||!sources_live)return proof;
    const auto floor=std::min(c.cutoff,c.lower);
    for(const auto& leaf:search.leaves()){
        if(leaf.parent_replaced||leaf.status==ControllingLeafStatus::Replaced||
           leaf.status==ControllingLeafStatus::Coalesced)continue;
        // Uncovered leaves retain their old bounds. Scope is not inferred
        // from "first artifact". Every source is bound to the complete root.
        if(leaf.gamma_L<c.gamma_L||leaf.gamma_U>c.gamma_U||leaf.cutoff>c.cutoff)continue;
        std::string reason;
        if(!proof.mergeValidLowerBound(leaf.id,floor,"round154_own_root_floor",&reason))
            throw std::runtime_error("round154_proof_merge:"+reason);
    }
    return proof;
}

inline void round154WriteLedger(const std::filesystem::path& path,
    const ControllingLeafScheduler& search,const ControllingLeafScheduler& proof,
    bool sources_live){
    if(!round154Enabled())return;
    const auto& c=round153();std::ofstream f(path);f<<std::setprecision(17)
      <<"{\"schema\":\"round154-proof-placement-v1\",\"root_complete\":"<<(round154().complete_root?"true":"false")
      <<",\"source_qualified\":"<<(c.accepted?"true":"false")<<",\"sources_live\":"<<(sources_live?"true":"false")
      <<",\"root_source_SHA\":"<<std::quoted(c.root_source_sha)<<",\"root_cutoff\":"<<c.cutoff
      <<",\"floor\":"<<c.lower<<",\"cutoff_complement_floor\":"<<std::min(c.cutoff,c.lower)
      <<",\"raw_search_L\":"<<search.globalLowerBound()<<",\"proof_L\":"<<proof.globalLowerBound()
      <<",\"proof_stopped\":"<<(round154().stopped?"true":"false")
      <<",\"native_floor_rows\":0,\"AM_uses_search_bounds\":true,\"leaves\":[";
    bool comma=false;
    for(const auto& leaf:search.leaves()){
        const auto* p=proof.findLeaf(leaf.id);if(!p)throw std::runtime_error("round154_proof_leaf_missing");
        if(comma)f<<',';comma=true;
        f<<"{\"id\":"<<std::quoted(leaf.id)<<",\"gamma_L\":"<<leaf.gamma_L<<",\"gamma_U\":"<<leaf.gamma_U
          <<",\"cutoff\":"<<leaf.cutoff<<",\"raw_search_lower\":"<<leaf.lower_bound<<",\"proof_lower\":"<<p->lower_bound<<'}';
    }
    f<<"]}\n";f.close();if(!f)throw std::runtime_error("round154_proof_ledger_write");
}
}
