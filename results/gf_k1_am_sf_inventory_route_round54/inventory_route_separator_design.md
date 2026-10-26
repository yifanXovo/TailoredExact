# Exact inventory-route separator design

At a root solution define `c_uv = sum_k Q_k x*_kuv`. Separation is an exact maximum-closure problem over station membership; the depot is fixed outside.

For inbound separation, station weights are `Y_i* - b_i`. Each directed station arc is reversed with capacity `c_uv`, so a source-side subset pays exactly the capacity entering it. Depot-to-station capacity is represented by a station-to-sink arc. Positive node weights become source-to-station capacities and negative weights station-to-sink capacities. The maximum score is total positive weight minus the deterministic minimum-cut value.

For outbound separation, station weights are `b_i - Y_i*`. Original station-arc orientation is used, and station-to-depot capacity is represented by a station-to-sink arc, so the source-side subset pays capacity leaving it.

Projected separation uses the same boundary constructions with weights `L_i-b_i` or `b_i-U_i`; nonpositive projected demand is discarded. Each result is reconstructed from the source side and evaluated again using original LP values. The scaled certificate tolerance is derived only from the frozen `1e-7` certificate tolerance and coefficient magnitude; it is not fitted to an instance.

The flow graph, edge insertion order, station order, augmenting search, and source-side extraction are deterministic. Canonical signatures include direction, scope, sorted subset, normalized coefficients, and right-hand side. Empty subsets are rejected; the full station subset is permitted because the depot remains outside. Duplicate signatures are rejected, and an interval-projected row is rejected when the accepted mixed row on the same subset and direction dominates it.

The root procedure repeatedly builds a fresh continuous F0-CLEAN model containing the complete accepted pool, solves it, separates the exact inbound and outbound problems, validates new rows, and reoptimizes. It stops mathematically only at no strict violation or LP infeasibility—never by elapsed time, nodes, size, or an instance-specific rule. The terminal integer model is another fresh F0-CLEAN build with the validated pool, callback off, default PreCrush, and native Gurobi branching. LP reads, simplex work, closure time, terminal-MIP work, and end-to-end process time are recorded separately.
