#pragma once
#include <cmath>
#include <string>
#include "FixedIntervalMipBackend.hpp"

namespace ebrp {
// Native status, local closure, and global certification are distinct.
struct Round107ScopeFacts {
    bool error = false, unresolved = false, native_optimal = false;
    bool native_infeasible = false, final_mode_verified = false;
    bool domain_witness_embeds = false, bound_available = false;
    bool target_requested = false, target_observed = false;
    double bound = 0, own_global_ub = 0, target = 0, tolerance = 1e-7;
};
struct Round107ScopeDecision {
    bool valid = true, close_by_dominance = false, empty_improvement_domain = false;
    bool target_reached = false, stop_whole_run = false;
    std::string reason = "open_local_obligation";
};
inline Round107ScopeDecision decideRound107Scope(const Round107ScopeFacts& f) {
    Round107ScopeDecision d;
    if (f.error || !std::isfinite(f.own_global_ub) ||
        (f.bound_available && !std::isfinite(f.bound))) {
        d.valid = false; d.stop_whole_run = true; d.reason = "ERROR_scope_or_numeric"; return d;
    }
    if (f.unresolved) {
        d.stop_whole_run = true; d.reason = "UNKNOWN_unresolved_whole_run_stop"; return d;
    }
    if (f.native_infeasible) {
        if (f.domain_witness_embeds) {
            d.valid = false; d.stop_whole_run = true; d.reason = "ERROR_excluded_domain_witness";
        } else { d.empty_improvement_domain = true; d.reason = "audited_local_INF"; }
        return d;
    }
    if (f.native_optimal) {
        if (!f.final_mode_verified || !f.bound_available) {
            d.valid = false; d.stop_whole_run = true; d.reason = "ERROR_unverified_native_OPTIMAL";
        } else if (f.bound + f.tolerance >= f.own_global_ub) {
            d.close_by_dominance = true; d.reason = "local_bound_dominance";
        } else {
            // No artificial target/requeue: the same-epoch terminal obligation remains.
            d.stop_whole_run = true; d.reason = "native_OPTIMAL_without_local_closure";
        }
        return d;
    }
    d.target_reached = f.target_requested && f.target_observed && f.bound_available &&
        std::isfinite(f.target) && f.bound + f.tolerance >= f.target;
    if (d.target_reached) d.reason = "qualified_local_mathematical_target";
    return d;
}
} // namespace ebrp
