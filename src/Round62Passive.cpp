#include "Round62Passive.hpp"
#include <algorithm>
#include <cmath>

namespace ebrp {
bool round62PassiveMode(const std::string& mode) {
    return mode == "passive-observe" || mode == "passive-cert";
}
Round62PassiveDecision evaluateRound62Passive(const Round62CoverageSnapshot& s,
                                             double active_bound) {
    Round62PassiveDecision out;
    auto reject = [&](const char* why) { out.reason=why; return out; };
    if (!s.archive_verified || !std::isfinite(s.archive_ub) ||
        !std::isfinite(s.control_ub) || s.control_ub < 0 || s.archive_ub < 0)
        return reject("unverified_upper_bound");
    if (!s.root_coverage || !s.tree_coverage || s.leaves.empty())
        return reject("incomplete_coverage");
    if (s.epoch != s.request_epoch) return reject("stale_epoch");
    if (s.tolerance < 0 || !std::isfinite(s.tolerance)) return reject("invalid_tolerance");
    if (!std::isfinite(s.root_lower) || !std::isfinite(s.root_upper) ||
        s.root_upper<s.root_lower || !std::isfinite(s.request_cutoff))
        return reject("invalid_root_or_request_scope");
    // The omitted G range contains only F >= U_control because P >= 0.
    // root_upper may instead be the physical maximum G, (n-1)/n.
    if (s.root_lower > s.tolerance) return reject("missing_low_gini_range");
    std::vector<const ControllingLeaf*> live;
    bool active_found=s.active_leaf.empty();
    double bound=s.control_ub;
    for (const auto& leaf:s.leaves) {
        if (leaf.parent_replaced || leaf.status==ControllingLeafStatus::Replaced ||
            leaf.status==ControllingLeafStatus::Coalesced) continue;
        live.push_back(&leaf);
        if (leaf.status==ControllingLeafStatus::Invalid ||
            !std::isfinite(leaf.gamma_L) || !std::isfinite(leaf.gamma_U) || !std::isfinite(leaf.cutoff) ||
            !leaf.parent_child_coverage_valid || std::isnan(leaf.lower_bound) ||
            (!std::isfinite(leaf.lower_bound) && leaf.status!=ControllingLeafStatus::Empty) ||
            leaf.cutoff + s.tolerance < s.control_ub)
            return reject("invalid_leaf_scope_or_bound");
        double b=leaf.status==ControllingLeafStatus::Empty ? s.control_ub : leaf.lower_bound;
        if (leaf.id==s.active_leaf) {
            active_found=true;
            if (s.model_identity.empty() || std::fabs(s.request_cutoff-s.control_ub)>s.tolerance)
                return reject("active_model_scope_mismatch");
            if (std::isfinite(active_bound)) b=std::max(b,active_bound);
        }
        bound=std::min(bound,b);
    }
    if (!active_found) return reject("active_leaf_not_in_live_coverage");
    std::sort(live.begin(),live.end(),[](auto a,auto b){return a->gamma_L<b->gamma_L;});
    double covered=s.root_lower;
    for (auto leaf:live) {
        if (leaf->gamma_L > covered+s.tolerance || leaf->gamma_U < leaf->gamma_L)
            return reject("uncovered_leaf_range");
        covered=std::max(covered,leaf->gamma_U);
    }
    if (covered+s.tolerance<s.root_upper) return reject("uncovered_root_tail");
    out.lower_bound=bound;
    out.usable_ub=std::min(s.control_ub,s.archive_ub);
    if (!std::isfinite(bound) || bound>out.usable_ub+s.tolerance)
        return reject("bound_witness_inconsistency");
    out.valid=true;
    out.certified=out.usable_ub-bound<=s.tolerance;
    out.reason=out.certified?"complete_coverage_external_gap_closed":"external_gap_open";
    return out;
}
} // namespace ebrp
