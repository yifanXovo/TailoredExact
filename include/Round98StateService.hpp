#pragma once
#include "Instance.hpp"
namespace ebrp {
inline bool round98IsIsolatedENS(const SolveOptions& o) {
    if(o.round98_state_service=="off")return true;
    return (o.round98_state_service=="aggregate"||o.round98_state_service=="projected"||
        o.round98_state_service=="vehicle-state")&&
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
