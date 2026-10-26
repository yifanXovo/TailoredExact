# Station-state formulations

Round 55 studies exact extended formulations for the fixed-interval relation between the Gini variable \(G\), a station's integer final inventory \(Y_i\), and the product \(Z_i=G Y_i\).  The stable `paper-k1-am-sf` preset continues to use the F0-CLEAN bit-product formulation.  All station-state variants are default-off research policies.

For the propagated integer domain \(\mathcal Y_i\), VD-P introduces selectors \(s_{iy}\) and perspective variables \(q_{iy}\):

\[
\sum_{y\in\mathcal Y_i}s_{iy}=1,\qquad
Y_i=\sum_y y s_{iy},\qquad
\ell s_{iy}\le q_{iy}\le u s_{iy},
\]

\[
\sum_y q_{iy}=G,\qquad
Z_i=\sum_y y q_{iy}.
\]

At integer selector points this is exactly \(Z_i=GY_i\).  Conversely, every feasible integer product point has the selector/perspective lift obtained by selecting its unique inventory state and assigning \(q_{iy}=G\) only there.  For an isolated station disjunction, the continuous selector relaxation is its standard perspective convex-hull representation.  This does not imply that the projection of the complete routing model is universally stronger or that a stronger root relaxation must solve faster.

VD-J extends VD-P by representing the ratio and satisfaction penalty on the same selectors.  It retains the existing absolute-deviation inequalities and adds the exact equality

\[
e_i=\sum_{y\in\mathcal Y_i}\left|y/D_i-1\right|s_{iy}.
\]

Both formulations enumerate only the actual propagated integer inventory domain, exclude unreachable states and invalid binary codes, reconstruct \(G\) and \(Z_i\) exactly, and use no instance-, size-, seed-, time-, or result-based dispatch.  They add no empirical parameter.  The source policies are `round55-vd-p` and `round55-vd-j`; the K1 research preset for the former is `research-k1-am-sf-vdp`.

The Round 55 proofs and projection mapping are in `results/gf_k1_am_sf_station_state_chain_round55/station_state_exactness_proof.md`, `station_state_convex_hull_proof.md`, and `station_state_projection_mapping.md`.
