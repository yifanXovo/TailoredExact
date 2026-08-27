# External K2 versus static K2 Core

This is the fixed-granularity causal comparison. Both arms use the same two
midpoint intervals and complete interval-local row packs. External-K2-Fixed
uses two independent native MIP jobs; ST-K2-P-Core uses one static segmented
native tree.

- Development pairs: 10.
- Geometric mean static/external Work ratio: 1.026238.
- Geometric mean shifted exact-time ratio: 1.028505.
- Material Work wins for the static tree: 4.
- Material Work wins for the two external trees: 6.
- False certificates: 0.

The per-instance table records exact time, Work, nodes, model size, proof-job
count, objective agreement, and certificate status. This comparison isolates
proof architecture at K2 and is not used to attribute any K2-versus-K4 effect.
