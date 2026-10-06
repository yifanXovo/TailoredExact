# Round105 mathematical and implemented contract

This is ordinary logic-based feasibility decomposition in this BRP's interface,
not a new Benders theorem. Historical inventory/Held-Karp search, R60 fixed-Y
diagnoses, R61 full-fleet time/no-good diagnoses, R54 min-cut necessary rows and
R96 fixed-order quantity optimization are distinguished in
`review/history_mathematics.md`. R103/R104 necessary-resource preprocessing is
not used. P-GRB remains the principal benchmark, ENS-C the protected reference.

## Global master and objective embedding

After the unchanged self-paid ENS-C startup obtains verified U0 and routes,
write the strengthened canonical VD-P/F0 at gamma=[0,min(1,U0)] with objective
cutoff U0 and epsilon=0. This covers every optimum: the objective is
nonnegative G+lambda*P, and an optimum is <=U0. The original physical witness
maps to every column and is checked against every native linear row. The
master retains every row, coefficient, bound and objective; only explicitly
enumerated arc x and node-load integer columns become continuous. ord and
conn already are continuous. Y, all one-hot state selectors, z, mode and p/d
retain their original integer declarations. `variables.csv` is the actual
indexed type readback, not a prefix-based type rewrite. There is one global
model, without AM. ENS's AM policy is unchanged.

For any original solution in this non-strict improving domain, choose its
actual routes, prefix loads and order, standard flow, final inventories,
one-hot states, true pair deviations, penalty deviations, G=Gtrue, and
state_g=G*state. All original rows hold by the inherited F0 contract; relaxing
types preserves the point. Thus every original optimum is in M, with its
original objective. Metric qualification of strengthened F0 remains required.
General travel accepted by a standalone oracle does not enlarge that class.

At integer selectors, exactly one state is active. The perspective bounds
and sum(state_g)=G force its state_g to G and all other state_g to zero.
Consequently zprod=G*Y exactly. Pair epigraphs and the original Gini row imply
G>=sum(i<j)|r_i-r_j|/(n*sum r_i) for positive sum; at zero sum the original
Gtrue=0 convention and G>=0 apply. Penalty epigraphs dominate true deviations.
The model objective cannot be below F(Y). G at arbitrary relaxed points is
still an epigraph, not asserted equal to Gtrue. Each optimal integer candidate
is checked against recomputed F(Y) at 1e-7. Any mismatch is an ERROR and stops;
it never produces a route UB, a cut or a repeated solve without information.

## All-order single-car oracle

The implemented oracle is a deliberately simpler all-original-station
physical template. It has local binary visit/direction/arcs, integer p/d,
continuous order/load, station-domain quantity bounds, one-direction nonzero
service, degree rows, balanced depot degree <=1, MTZ, prefix recurrences and
travel+(cp+cd)*sum pickup<=T. It has no inventory/Gini/penalty/cutoff block and
no other-car obligation. Every original directed arc is present.

Every physical local route embeds with its visit/order/load. MTZ excludes
station-only cycles; degree balance then recovers the sole depot tour or an
empty route. For V stations, ord in [0,V] and MTZ coefficient V+1 leave
inactive arcs valid even between an unvisited node and the last stop. Load
recurrences use 2Q: difference load_j-load_i-p_j+d_j is in [-2Q,2Q] on the
unconditional box; on active arcs it is zero. Continuous loads become exact
integer prefixes once route and operations are integral. A return arc imposes
no empty-load condition. Total pickup may exceed Q. The nonzero service rule
forbids transit-only visits; absent stations cannot be shortened-path transit
in the fixed mode. All external helpers remain available in the free template.

A complete local mode fixes z=1,p,d for each served station and z=0 for each
absent station. These named rows are the only difference between complete and
released-core templates. Given an integral master mode, p=(b-Y)+ and d=(Y-b)+
and unique service are checked explicitly. A full oracle route is independently
checked by the original strict physical wrapper, padded with empty other-car
records. MIP objective zero needs no shortest-travel proof. A valid route is
FEASIBLE; only completed native INFEASIBLE is PROVED_INFEASIBLE. Limits,
INF_OR_UNBD, numerical trouble and missing solutions are not impossibility.

## Conflicts and helpers

For all mode assumptions, Delta=sum(served)[(1-z)+(1-state_y)] +
sum(absent)z. Delta>=1 removes precisely the same complete car mode. Every
term is nonnegative on integer master states; Delta=0 enforces the proved
impossible membership and quantities. A changed inventory, changed ownership
or added helper produces a mismatch. Therefore every original solution
satisfies the cut. The row is local, not a global Y no-good.

The universal all-station template's IIS proposes semantic station groups.
Any selected z/p/d assumption row retains the ENTIRE station group. Served
groups map to BOTH z_ki=1 and state_i,y=1; absent groups map to z_ki=0, without
fixing global Y_i. All unmentioned assumptions are removed by rebuilding the
same full template and reoptimizing it. Only another INFEASIBLE status admits
the shorter core; numerical/limit uncertainty retains the proved full mode.
The linear row is sum(served core)(z+state)-sum(absent core)z <=2*served-1.
This is exactly conjunction exclusion, with no threshold/superset/symmetry
extension. The actual current master point must violate it by about one;
the original full Start must satisfy it. IIS is an irreducible proposal,
not minimum cardinality, an LP Farkas proof, or a rational MIP certificate.

Counterexample B is independently enumerated: Q3 operations (+2,+2,-3)
require +2 first and cannot take either remaining operation. Adding -1 allows
loads 2,1,3,0. The naive served-only cut removes that route; the complete
absence-inclusive row permits it. Counterexample A has a single pickup4
supplier, forcing all four deliveries onto its vehicle. Full travel10 plus
handling8 exceeds T16, though singleton10 and three-anchor14 necessary bounds
hold. At T18 a legal route exists. Two integer vehicle assignments cannot
fractionally share the supplier. These are correctness qualifications, not
performance contributions or proof of real-row increment.

## External exact loop, bounds and finite termination

Every Optimize and IIS call is serial and recorded before/after execution.
Each call receives only the remaining process-wide work deadline; diagnostics'
outer caps never become per-car production budgets. No callback Optimize,
timer restart, Work/iteration cap or ENS fallback exists. A master without an
optimal certificate exits UNKNOWN with any qualified ObjBoundC. It does not
route-check a nonoptimal candidate in production. Native per-model parameters
retain Threads1/Seed0/PresolveAuto, zero gaps and original tolerances. Incumbent
rows and native quality attributes are checked after each solve; numerical
trouble is an ERROR. Proofs are scoped floating Gurobi engineering evidence.

For an optimal integer master mode, each car is checked using a run-local
cache bound to every operation, Q/T/handling, initial/capacity, all travel and
the unchanged numeric contract. One proved failure yields a retained cut and
new Optimize; this event has new mathematical information and is not a timed
restart or tree-retention claim. A needed UNKNOWN ends the entire loop. A
deadline during optional core work retains the already-proved full conflict.
All cars feasible gives a complete strict physical witness and original F.
It certifies only when the master lower bound closes at 1e-7. Failure to close
is a model/mapping ERROR. The strongest qualified master bound is retained
after valid cuts; no local route bound is an F bound. LB>verified UB or a
master infeasible despite its mapped known witness is an ERROR, without
clipping or an infeasibility shortcut.

There are finitely many bounded integer inventories and vehicle memberships.
Each infeasible round cuts its current mode, hence its fleet candidate. A
feasible optimal round closes or errors. A repeated identical fleet candidate
is an explicit ERROR, with no arbitrary repetition limit. This finite
termination argument does not imply polynomial complexity or good costs.
Handled C++ exceptions preserve the current result state, logs and durable
error record; graceful UNKNOWN retains the paid UB and valid master LB.
An external hard kill cannot execute finalization. The first F5 600s
diagnostic was killed by the unchanged cap-2 supervisor after its native
TimeLimit log, before after-call/quality/solution/summary persistence. It has
no qualified endpoint and is retained as a charged failure, without log-based
bound recovery. The retry and subsequent contemporary comparisons use the
existing 30s whole-process shutdown reserve (same reserve for every paired
arm). This is a work/finalization boundary within the original total budget,
not a per-car limit, new timer or change to physical T or numeric tolerances.
It does not establish graceful handling of every conceivable external kill.

Primary references: [Gurobi 13 C solving/IIS API](https://docs.gurobi.com/projects/optimizer/en/current/reference/c/solving.html),
[Gurobi IIS guide](https://support.gurobi.com/hc/en-us/articles/15656630439441-How-do-I-use-compute-IIS-to-find-a-subset-of-constraints-that-are-causing-model-infeasibility),
[Hooker and Ottosson 2003](https://doi.org/10.1007/s10107-003-0375-9), and
[Erdoğan et al. 2015](https://doi.org/10.1016/j.ejor.2015.03.043).
The latter's bicycle model admits different service semantics, so its cuts
are not imported. Installed header and runtime are 13.0.2, pinned per run.
