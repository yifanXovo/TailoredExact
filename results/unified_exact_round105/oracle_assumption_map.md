# All-station oracle assumptions and cut map

The original station IDs and complete local operation vector are in
`patterns.csv`. Each `pattern_I_kK/full.lp` contains the entire generic local
physical template and its explicitly named assumption rows. No global
inventory, objective cutoff, Gini or other vehicle obligation is present.

| Semantic group | Actual technical rows | Meaning | Master conjunction |
|---|---|---|---|
| Served i, signed operation qi!=0 | a_i_z: z_i=1; a_i_p: p_i=max(qi,0); a_i_d: d_i=max(-qi,0) | This car serves exactly the fixed operation | z_ki=1 AND state_i,(bi-qi)=1 |
| Absent i, qi=0 | a_i_z: z_i=0 | This car does not serve i | z_ki=0, with global Yi free for another car |

IIS row membership is translated to whole station groups. Fixed operation
rows never become a global-Y-only literal. All variable bounds are generic
physical bounds; none is a hidden pattern fixation. If the IIS mentions one
row in a served group, the master cut conservatively includes both z and
state, irrespective of which technical rows the IIS happened to select.

`proposal.ilp` and `proposal.json` preserve the numerical IIS and its whole
group proposal. `core_confirm.lp` is freshly built with only those groups;
all unmentioned station variables/arcs/quantities are actually free again.
`core_confirm.lp.log`/calls.csv must contain native INFEASIBLE before the
shorter core is marked confirmed. An IIS retaining all groups uses the
already proved complete mode. IISMinimal is recorded but not used as a
minimum-cardinality or proof criterion. Interrupted/unqualified core work
retains the already-proved full mode, with its actual scope and costs.

For a core with a served groups and b absent groups, the submitted inequality
is sum(served)(z+state)-sum(absent)z <=2a-1. Each absent group supplies a
negative coefficient. This equals the requested mismatch>=1. The current
optimal master candidate must violate it by about one; the complete known
feasible Start must satisfy it. `conflicts.csv` retains every actual column,
coefficient, RHS, group count and confirmation flag. No row is generalized
to operation thresholds, service supersets or other vehicle labels.

A feasible full oracle writes a native solution and its route is checked by
the original strict physical verifier. Cache keys bind all operations,
vehicle/Q, T, handling, station initial/capacity data, all travel and the
unchanged numerical contract; caches exist only in the current execution.
The final complete route set is independently verified again and written
as witness.json. `seed.json` is the run's own paid initial route set.
