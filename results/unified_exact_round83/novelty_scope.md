# Narrow prior-art check and contribution scope

Taillard, Badeau, Gendreau, Guertin and Potvin (1997), *A Tabu Search Heuristic
for the Vehicle Routing Problem with Soft Time Windows*, Transportation Science
31(2),170-186, already uses exchanges of consecutive customer segments between
two routes. The publisher abstract was directly read on2026-09-17 Asia/Shanghai;
this specific observation is supported by the abstract, not a claimed full-paper
review. [Publisher and DOI](https://pubsonline.informs.org/doi/10.1287/trsc.31.2.170).

Therefore R83 does not claim invention of inter-route segment exchange. Its
scope is an implementation and evaluation of an equal-signed-net-load restriction,
two recipient-prefix checks, exact inventory-preserving duration descent and
composition with the existing strict inventory closure in this BRP. These
properties follow from the stated mathematics and original semantic checks;
they do not establish that this particular restricted rule is absent from
all prior literature. No exhaustive novelty claim or general speed theorem.

The cited paper studies time-window routing and tabu search. R83 retains this
project's original inventory/Gini objective, empty departure and legal loaded
return, and passes only verified current-run witnesses to a complete Gurobi
MIP proof method. This distinction explains implementation scope; it is not
by itself proof of theoretical novelty. Full-method benefit remains empirical.
