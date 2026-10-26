#pragma once
#include "Instance.hpp"
namespace ebrp {
// Round99 separates representation from redundant quantity declarations.
// q-integer (Q-I): project m, retain integer p/d.
// m-binary (M-B): retain binary m and its original rows, continuous p/d.
inline bool round98KnownStateService(const std::string& mode) {
    return mode=="off" || mode=="aggregate" || mode=="projected" ||
        mode=="vehicle-state" || mode=="q-integer" || mode=="m-binary" || mode=="m-binary-linked";
}
inline bool round98ProjectsDirection(const std::string& mode) {
    return mode=="projected" || mode=="vehicle-state" || mode=="q-integer";
}
inline bool round98ContinuousQuantities(const std::string& mode) {
    return mode=="projected" || mode=="vehicle-state" || mode=="m-binary" || mode=="m-binary-linked";
}
inline bool round99LinksDirection(const std::string& mode) { return mode=="m-binary-linked"; }
inline bool researchChecksPhysicalQuantities(const SolveOptions& o) {
    return o.round100_continuous_quantities || o.round98_state_service != "off";
}
inline bool round98IsIsolatedENS(const SolveOptions& o) {
    if(o.round98_state_service=="off" && !o.round100_continuous_quantities)return true;
    if(o.round100_continuous_quantities && o.round98_state_service!="off")return false;
    return round98KnownStateService(o.round98_state_service)&&
        o.algorithm_preset=="research-round83-vds-equal-net-exchange"&&
        o.method=="gcap-frontier"&&o.k1_am_sf_controller_enabled&&!o.plain_baseline&&
        !o.round66_arc_load_replacement&&!o.round65_budget&&o.round65_projection=="off"&&
        o.round63_time_mode=="off"&&o.round64_shared_mode=="off"&&
        !o.round88_constructive_only_descent&&!o.round89_native_ot_b1&&!o.round90_lp_g_split&&
        !o.round92_handling_activation&&!o.round96_route_order&&o.round97_native_closure=="off"&&
        o.round60_candidate_mode=="off"&&o.round61_candidate_mode=="off"&&
        o.round62_threshold_mode=="off"&&o.external_gini_interval_mip_policy=="round55-vd-p"&&
        o.external_gini_scheduling=="round31-nonblocking-native-bound";
}
}
