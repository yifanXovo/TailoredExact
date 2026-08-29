# Algorithm lineage

This file distinguishes the current algorithm from historical research lines.

| Line | Role after Round 54 | Relationship to K1-AM-SF |
|---|---|---|
| Early compact CPLEX and route-load BPC | Historical/contextual | Superseded as the paper-facing mainline |
| Gini-frontier compact/tailored callback BC | Historical research | Supplied interval-ledger and formulation infrastructure; callback mechanisms are not active |
| Round 47 K1 adaptive-mass | Controller ancestor | Supplies K0=1, midpoint, adaptive-mass score, `tau=0.08` |
| Round 50 interval-MIP v0 | Inner-backend ancestor | Supplies the fixed-interval MILP |
| Round 51/52 exhaustive Big-M and dynamic cuts | Rejected/default-off research | Not active in K1-AM-SF |
| Round 53 K1-AM-F0/F0-CLEAN | Direct stable candidate | Semantically identical to Round 54's named mainline |
| Round 54 K1-AM-SF | Stable mainline | Canonical preset `paper-k1-am-sf` |
| Round 54 IR1/IR2/IR3 | Bounded research | IR1/IR2 audited offline; IR1 failed live Stage A; IR3 not opened |

The rename from K1-AM-F0 to K1-AM-SF is an identity/documentation freeze, not
an algorithm change. Historical aliases remain valid so old commands can be
reproduced without silently changing their semantics.
