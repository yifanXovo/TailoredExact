# Isolated station-state convex hull

For each allowed value (y\in\mathcal Y_i\), define the segment

\[
S_y=\{(G,Y,Z):\ell\le G\le u,\ Y=y,\ Z=yG\}.
\]

The VD-P equations use convex multipliers (s_y\ge0),
\(\sum_y s_y=1\), and disaggregated variables
\(q_y=s_yG_y\) with \(\ell s_y\le q_y\le u s_y\).  They reconstruct

\[
G=\sum_y q_y,\qquad Y=\sum_y ys_y,\qquad Z=\sum_y yq_y.
\]

Every point in this extended relaxation is therefore a convex combination of
points in the segments (S_y): for (s_y>0), take
\(G_y=q_y/s_y\); zero-weight states are irrelevant.  Conversely, every convex
combination of segment points supplies variables satisfying these equations.
Thus the continuous selector relaxation is an exact extended formulation of
\(\operatorname{conv}(\bigcup_y S_y)\).

Projecting this hull onto only ((G,Y,Z)) does not automatically make value
disaggregation stronger than the aggregate McCormick envelope over a
continuous box; for that isolated bilinear graph the two projections may
coincide.  VD-J's expected additional strength comes from using the same state
weights for inventory, product, ratio, and penalty.  That joint consistency,
not the name “value disaggregation,” is the hypothesis tested by the root and
live censuses.
