# Round 39 unresolved official row

`primary__round39_small_hard_V12_M3_Q20_slot07_seed621538683__c6_hga_light_1000` is **not** reported as optimal or strict. Two independent Seed-0
runs close all four relevant leaves with zero open leaves, complete lifecycle,
monotone valid bounds, and the identical endpoint LB
`0.64711627538070693` versus verified UB
`0.64711643345550207`. The absolute residual
`1.5807479514240441e-07` exceeds the frozen `1e-7` certificate tolerance, so both runs
correctly reject with `global_bound_gap_not_closed` after about 76 to 78 seconds.
Because the tree is already closed, this is not a timeout and further wall time
does not provide a continuation state. Both attempts and hashes are retained.
