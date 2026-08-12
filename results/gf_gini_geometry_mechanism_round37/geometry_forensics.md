# Structural Gini-geometry forensics

Round 36 contains 14 default-HGA geometry witnesses. The weakest
complete initial LP cell is interior (cell 1 or 2) in
12/14 instances: the index
counts are `{1: 7, 2: 5, 0: 2}`. This rejects a generic rule that simply
packs more intervals near zero Gini.

The wide-anchor intervention exposed a geometry change in
13/14 instances and changed the
downstream sequence in 11/14, but its
causal outcomes were bidirectional (`{'left_win': 10, 'right_win': 4}`). Geometry is
therefore a real mechanism, while wider anchoring is not a supported policy.

The supported next hypothesis is **pilot weakest-cell pre-refinement**: solve
the four existing initial LPs completely, select the open cell with the lowest
valid LP bound using structural tie breaks, split it once at its midpoint, and
then resume unchanged C6 scheduling. The rule is independent of instance
labels, elapsed time, Work, nodes, and hardware. Exactness follows from complete
LP validity plus exact parent-child coverage; the test is about proof-search
quality, not correctness.
