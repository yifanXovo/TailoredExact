# Saved R129 B20 coverage example

This is the original E2 MS2 Seed0 diagnostic, not a Round130 formal observation. Its own H already attains F=0.5773330699702928; that feasible witness alone proves no optimality. Three subsequent natural splits and their actual closure sources provide the coverage. No old solution or bound enters a Round130 producer.

## initial_decomposition_ledger.csv

| anchor_cell_index | anchor_lower | anchor_upper | active | active_lower | active_upper | truncated_by_proof_range | U_proof_launch | U_anchor_launch | proof_range_lower | proof_range_upper | normalization_source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | 0.57733306997029277 | 1 | 0 | 0.57733306997029277 | 0 | 0.57733306997029277 | 0.57733306997029277 | 0 | 0.57733306997029277 | proof |

## split_decision_ledger.csv

| parent_id | eligible | decision_valid | split | child_infeasibility_trigger | strict_bound_trigger | normalized_disjunction_gain | parent_native_bound_target | target_phase_required | reason | b_plus | eta_proof | eta_anchor | normalization_source | normalization_upper_bound |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| L0 | true | 1 | 1 | 1 | 0 |  |  | 0 | adaptive_mass_preserve_child_infeasibility_split | 0 |  |  | proof | 0.57733306997029277 |
| L0.0 | true | 1 | 1 | 1 | 0 |  |  | 0 | adaptive_mass_preserve_child_infeasibility_split | 0 |  |  | proof | 0.57733306997029277 |
| L0.0.1 | true | 1 | 1 | 1 | 0 |  |  | 0 | adaptive_mass_preserve_child_infeasibility_split | 0 |  |  | proof | 0.57733306997029277 |
| L0.0.1.0 | true | 1 | 0 | 0 | 0 | 0.0013341872971890146 | 0.5269579311675191 | 1 | adaptive_mass_score_below_tau_native_target | 0.5269579311675191 | 0.0013341872971890146 | 0.0013341872971890146 | proof | 0.57733306997029277 |
| L0.0.1.0 | true | 1 | 0 | 0 | 0 | 0 |  | 0 | adaptive_mass_no_strict_child_improvement | 0.5269579311675191 | 0 | 0 | proof | 0.57733306997029277 |

## paper_leaf_ledger.csv

| leaf_id | parent_id | depth | child_index | gamma_L | gamma_U | base_lower_bound | lower_bound | status | lp_complete | lp_optimal | lp_infeasible | lp_bound | terminal_mip_started | terminal_ready | coalesced_block_id | coverage_member_ids | c6_native_phase_count | c6_frontier_milestone_reached | c6_children_ready | single_child_contraction_parent | strict_infeasible_half_verified | contracted_infeasible_gamma_L | contracted_infeasible_gamma_U | contraction_source | closure_source | lower_bound_sources |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| L0 |  | 0 | -1 | 0 | 0.57733306997029277 | 0 | 0.47907642185207561 | replaced | 1 | 1 | 0 | 0.47907642185207561 | 0 | 0 |  |  | 0 | 0 | 0 | 0 | 0 |  |  |  |  | objective_nonnegative_penalty_G_floor;optimal_complete_lp_relaxation |
| L0.0 | L0 | 1 | 0 | 0 | 0.28866653498514638 | 0.4802765562667401 | 0.4802765562667401 | replaced | 1 | 1 | 0 | 0.4802765562667401 | 0 | 0 |  |  | 0 | 0 | 0 | 0 | 0 |  |  |  |  | inherited_parent_lp_bound;optimal_complete_child_lp_relaxation |
| L0.1 | L0 | 1 | 1 | 0.28866653498514638 | 0.57733306997029277 | 0.47907642185207561 | 0.57733306997029277 | empty | 1 | 0 | 1 | 0 | 0 | 0 |  |  | 0 | 0 | 0 | 0 | 0 |  |  |  | complete_child_lp_infeasible | inherited_parent_lp_bound |
| L0.0.0 | L0.0 | 2 | 0 | 0 | 0.14433326749257319 | 0.4802765562667401 | 0.57733306997029277 | empty | 1 | 0 | 1 | 0 | 0 | 0 |  |  | 0 | 0 | 0 | 0 | 0 |  |  |  | complete_child_lp_infeasible | inherited_parent_lp_bound |
| L0.0.1 | L0.0 | 2 | 1 | 0.14433326749257319 | 0.28866653498514638 | 0.52689063150688198 | 0.52689063150688198 | replaced | 1 | 1 | 0 | 0.52689063150688198 | 0 | 0 |  |  | 0 | 0 | 0 | 0 | 0 |  |  |  |  | inherited_parent_lp_bound;optimal_complete_child_lp_relaxation |
| L0.0.1.0 | L0.0.1 | 3 | 0 | 0.14433326749257319 | 0.21649990123885979 | 0.52689063150688198 | 0.57733306997029255 | closed | 1 | 1 | 0 | 0.52689063150688198 | 1 | 1 |  |  | 1 | 0 | 0 | 0 | 0 |  |  |  | native_terminal_mip_optimal | inherited_parent_lp_bound;optimal_complete_child_lp_relaxation;valid_child_target_native_bound;native_terminal_mip_bound |
| L0.0.1.1 | L0.0.1 | 3 | 1 | 0.21649990123885979 | 0.28866653498514638 | 0.52689063150688198 | 0.57733306997029277 | empty | 1 | 0 | 1 | 0 | 0 | 0 |  |  | 0 | 0 | 0 | 0 | 0 |  |  |  | complete_child_lp_infeasible | inherited_parent_lp_bound |

The detailed immutable tree events, LP dispositions, root scope, all closed-side reasons and final terminal are indexed in R129_B20_coverage_example.json. Infeasibility of a model containing a semantic proof-closure row is interpreted only on its stated improving domain and original numerical policy; it is not inclusive-root physical infeasibility. Split exposure does not establish its net computational contribution.
