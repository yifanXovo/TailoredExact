# Revision 1 mathematical note: SF-R1

SF-R1 removes only the optional triple-support duration inequalities from
F0-CLEAN.  For vehicle `k` and a three-station support `S`, the removed row is
a valid strengthening inequality derived from a route-duration lower bound.
It is not used to define route variables, visits, pickup/drop feasibility,
inventory conservation, connectivity, the Gini interval, the exact product,
the penalty, the objective, or the certificate scope.

Let `F` be the complete integer-feasible set defined by the retained core
formulation and let `H_3` be the set of triple-support duration inequalities.
The existing validity proof establishes `F subseteq H_3`.  F0-CLEAN therefore
represents `F intersect H_3 = F`; deleting `H_3` leaves exactly `F`.  The
revision can weaken an LP relaxation and alter a solver trajectory, but it
cannot admit an integer solution that violates the original problem and
cannot remove an original feasible solution.  Pair-support duration rows and
every other F0-CLEAN family remain present.

The activation rule is uniform and parameter-free: under policy
`round55-sf-r1-remove-triple-duration`, the maximum enumerated static support
size is exactly two for every station count, vehicle count, capacity, input
path, seed, interval, and solve state.  No runtime observation participates in
the rule.

The revision was chosen only from the frozen family-resolved offline audit:
216,919 triple rows over 27 states, zero root-active rate, zero dual-nonzero
rate, zero strict root-bound contribution, and a 0.8687645295438094 geometric
mean root-LP Work ratio after removal.  Those facts justify a complete live
development test; they do not establish MIP improvement in advance.

SF-R2 is not opened.  Pair removal has the same validity status but a much
smaller footprint (21,294 rows) and a weaker root-LP Work ratio
(0.9337542984446626), so testing it would add a second mechanism direction
without stronger causal motivation.
