# Penalty-budget validity

For an interval with lower endpoint \(l\), verified incumbent \(\bar U\), certificate tolerance \(\varepsilon\), and objective

\[
G+\lambda_P P,
\]

every strict-improver solution satisfies

\[
l+\lambda_P P \le G+\lambda_P P < \bar U-\varepsilon.
\]

Thus, when \(\lambda_P>0\),

\[
P < (\bar U-\varepsilon-l)/\lambda_P.
\]

The implementation may safely use the weak budget

\[
P\le B_I=(\bar U-\varepsilon-l)/\lambda_P.
\]

With exact station-state selectors, \(P=\sum_{i,y}c_{iy}s_{iy}\), where
\(c_{iy}=w_i|y/D_i-1|\).  Therefore
\(\sum_{i,y}c_{iy}s_{iy}\le B_I\) is valid.  When \(\lambda_P=0\), no finite budget is inferred and the cover mechanism is disabled.

Round 55 did not open live penalty-budget experiments because VD-J (the required joint station-state formulation) failed fixed-interval development and did not pass confirmation.  This is a gate outcome, not a validity failure.
