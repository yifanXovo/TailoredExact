# 01 Problem Definition

The paper problem is the original ExactEBRP route-load optimization problem:

- routes start and end at the depot;
- every station is served at most once;
- vehicle capacity and route-duration constraints hold;
- station final inventories respect capacities;
- the objective is `G + lambda * P`, where `G` is the Gini component and `P`
  is the weighted target-ratio penalty.

Incumbents from native HGA-TGBC, local repair, route-pool recombination, compact
CPLEX, or imported plans are UB-only.  None may contribute lower-bound evidence.
