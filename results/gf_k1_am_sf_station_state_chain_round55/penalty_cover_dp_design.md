# Exact penalty-cover DP design

`PenaltyCoverSeparation` receives penalty costs and the budget in one proved exact integer scale.  It never rounds floating-point costs to integers.  The DP processes stations in canonical order and offers either no choice or one state choice per station.  Its cost state is saturated at \(B+1\), which is sufficient to distinguish noncovers from strict covers without overflow.  The additive objective is

\[
\sum_{(i,y)\in C}(1-s^*_{iy}).
\]

A cover cut is strictly violated exactly when the optimum is below one by the frozen tolerance.  Lexicographic signatures make ties deterministic.  Reconstruction removes redundant members to obtain an inclusion-minimal cover, validates the exact cost sum, and records a canonical signature.  Exclusion masks prohibit each previously accepted cover and every strict superset, giving duplicate-free one-pass or closure separation.

The dedicated Round 55 tests exercise exact reconstruction, strict-cover detection, minimalization, duplicate rejection, one-pass behavior, and termination.  The runtime census and live PC1/PC2 stages remain empty because their mathematical opening gate was not met.
