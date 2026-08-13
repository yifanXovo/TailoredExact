# Structural Gini-geometry conclusion

## What is established

The four initial Gini cells are not equally strong. Across the 14 prior C6/HH
forensic rows, the weakest complete LP cell was index 1 in seven rows, index 2
in five, and index 0 in only two. Thus a generic low-G skew was rejected before
new experiments: **12/14 bottlenecks were interior cells**.

G1 then tested the narrower causal statement. It completed the four initial LPs,
selected the open cell with the smallest valid LP bound under structural ties,
split it once at the midpoint, and resumed unchanged C6. In the 10 runs where
the policy was exposed, the independently derived prior weakest-cell index was
reproduced 10/10 and the post-split valid bound of that cell increased 10/10.
This is direct evidence that finite-width Gini-cell geometry causes a real,
localized relaxation loss.

## Why the fixed policy is not a general improvement

The magnitude of the local gain does not predict the global proof effect. The
V20 tight-T positive witness has a small local gain (`0.00160882`) yet improves
the paired common-UB final gap by `0.07526`, `0.10919`, and `0.11225` at 180,
480, and 900 seconds; common-window AUC improves at all three caps. Conversely,
the V50 high-imbalance witness has the largest local gain (`0.0545466`) but its
final gap regresses by about `0.028964` at all three caps and its AUC also
regresses.

This is consistent with exact-tree geometry rather than a contradiction. A
local split raises one cell's bound but also creates another open leaf, spends
two complete child LPs up front, and changes which leaf controls later native
targets and exact closures. The global lower bound is the minimum over all
relevant leaves. If the refined cell remains controlling and its children align
well with later closures, the local gain propagates (the V20 witness). If
another child or cell becomes the persistent bottleneck, the extra topology and
front-loaded census can delay more productive native-bound work (the V50
regression). The largest immediate local gain can therefore coexist with a
worse finite-window global proof trajectory.

## Decision

G1 demonstrates a real causal mechanism but fails the uniform downstream
benefit requirement. It is retained as a **default-off exploratory diagnostic**,
not promoted. G2 (multi-cell weakness-density geometry) remains an untested
future hypothesis; this round does not authorize or validate it. Any future
work would need a new predeclared rule that predicts downstream bottleneck
persistence using uniform structural information, rather than merely selecting
the currently weakest initial cell.

**C6-HGA-FULL with K=4 and rho=0.01 remains the mainline exact algorithm.**
