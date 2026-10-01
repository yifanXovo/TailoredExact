# Round99 two factors and correctness

Inherit R98 mathematical_algorithm.md original physics, G epigraph, interval cover,
cutoff complement, startup, numerical certification and all z/s/Y/load declarations.
No change to physical quantity validation, including unvisited p/d columns.

| Mode | CLI state/service | A/B | m | p/d |
|---|---|---|---|---|
| ENS-C | off | absent | B | I |
| R1 | aggregate | present | B | I |
| Q-I | q-integer | present | eliminated | I |
| M-B | m-binary | present | B | C |
| R2 | projected | present | eliminated | C |

Q-I adds redundant quantity integer declarations to R2. Integer s selects one
inventory y, A with balance gives P=(b-y)+, D=(y-b)+. Integer z with B and
sum z<=1 selects its unique service owner; all other quantities vanish by
the original visit upper bounds. Hence every p/d is already a physical integer.
Adding its declaration removes no integer solution. Recover old binary m=1
exactly when pickup>0, otherwise0. Both-zero caps fix quantities0; a=0 choose0;
c=0 and pickup>0 choose1. No division by zero or missing other-direction bound.

M-B only relaxes quantity declarations in R1. The identical s/z/A/B argument
still forces p/d integers. Its old binary m and all three direction rows remain.
Every original physical witness extends using its unique y/state and service;
every model integer solution reconstructs the same original physical solution.
The same routes, prefix loads, empty departure, loaded return and time expression
are preserved. Total pickup is not bounded by Q, nor station inventory conserved.

Relaxing ALL integer declarations makes R1 and M-B byte-identical numerical
matrices; Q-I and R2 likewise. The continuous m existence interval
p/a <= m <= z-d/c gives c p+a d <= a c z for positive a/c. Zero caps are covered
by retained individual bounds. Thus all four project identically on shared
coordinates. Column/row removal differs from pure type intervention, so two
arms alone cannot identify a unique binary-direction causal mechanism.

Actual writer traits independently determine projection and p/d VType; mode is
included in canonical full LP SHA, including declaration sections and ordered
native identity. Inherited native adapter captures actual VType array, relaxes
all types for LP and restores that captured array, never a fixed R1/R2 pattern.
Cache artifact SHA/epoch and per-adapter options remain bound to the actual mode.
Actual Starts must be remapped and all-row checked for each generated model.

Standalone Model.presolve diagnostics may differ from optimize internal model
and expose no uncrush mapping. Equal counts do not establish equal native models,
and surviving names do not license arbitrary vector reconstruction. Branching
variables and unique cut causes are unknown unless directly observed.
Sources: [Gurobi presolve explanation](https://support.gurobi.com/hc/en-us/articles/360024738352-How-does-presolve-work),
[Gurobi13 C solving API](https://docs.gurobi.com/projects/optimizer/en/current/reference/c/solving.html).
