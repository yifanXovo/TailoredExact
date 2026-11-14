# Certified decisions from the complete physical archive

The offline analysis recovers 50 complete physical fleet records, covering all
32 specified weight-study observations and 24 resource observations (six overlap).
No fleet is missing and no new solver is used. Every record keeps its original
method/Seed/run/source, original objective, qualification and clock. Full routes,
per-stop quantities, inventories, prefixes and loaded-return unloading are in
review/data_physical_archive.json, with fixed input/carrier/member hashes. Large
old coverage traces remain at their original pinned source; the new archive
retains their qualification summary and canonical parsed-cover hash.

Every fleet was independently checked for depot closure, unique nonzero one-way
service, inventory capacity/balance, empty departure, all load prefixes, vehicle
capacity, permitted loaded return and travel plus station/depot handling time.
True Gini and weighted relative deviation were recomputed from full inventories,
not rounded G/P table entries. Physical T/Q/inventory/target/capacity/coordinates
and normalized omega identity match inside all four parameter families. Cutoff,
auxiliary-g restrictions and propagated stock boxes are not new physical data.

## Parameter objects and numerical contract

For the same physical domain F and normalized weights, Omega=sum omega>0,
p=P/Omega, rho=lambda*Omega, and v(rho)=min_x[G(x)+rho*p(x)]. Every feasible fleet
defines an affine upper line. The minimum of all archive lines U_A is an upper
bound, not a producer result at every unrun weight or a complete Pareto frontier.
Objective-identical lines are grouped only for envelope calculation; full fleet
owners and dominated points remain in the archive.

The infimum of affine functions is concave. Thus endpoint *global physical*
lower bounds give a lower chord only on their endpoint interval. Same exact
coordinate uses the greatest qualified global lower and retains every contributing
source; no zero-length chord is formed. L_C is the maximum of applicable chords.
Every L used is the original completed run's qualified full-domain cover/cutoff-
complement result. No raw local LP, stock subdomain, true-G fragment, rejected
native source or incomplete cutoff bound is transplanted across objectives.

The original physical/numerical qualification is retained. To express a safe
analysis of the exact loaded coefficients, we reduce each original accepted
global L by 1e-7 and add 1e-12 to feasible objectives recomputed with exact rational
G and loaded binary64 weights. Coordinates are the exact loaded binary64 lambda
times the exact sum of loaded binary64 weights; original floating/display rho
is also preserved. This resolves, rather than rounds away, the X35 endpoints
displaying as .49999999999999994 and1.9999999999999998. The guards do not convert
native numerical certificates into rational optimization proofs.

The difference U_A-L_C is piecewise affine. All feasible-line intersections,
overlapping lower-chord intersections, chord endpoints and relevant crossings
are evaluated as rational numbers; maxima occur at those finite endpoints.
Because all distinct anchor pairs are used, L_C is continuous on the covered
range: a chord starting or ending at an interior anchor takes that anchor's
L value, which is also approached by an incoming or outgoing anchor chord;
all chords spanning the anchor are continuous there. Thus no larger
one-sided endpoint gap is lost by evaluating the closed partition endpoints.
There is no grid or Optimize. A negative difference would trigger a source/
error investigation; no clipping was used. The independently written review
algebra agrees, up to the explicit 1e-12 feasible-objective guard.

## Four continuous-range findings

| Family | Actual range (display) | Run records / component lines | Supported lines | Maximum archive regret upper bound |
|---|---|---|---|---|
| K-15-S | [.710502825,2.8420113] | 8 /3 | 3 | .0023562818631971206 |
| UC-B20-B | [.88725,3.549] | 6 /1 | 1 | .00000010000100032886562 |
| R-B20-S-T1 | [.5,2] | 9 /7 | 3 | .015594268604373972 |
| R-X35-S-T2 | [.49999999999999994,1.9999999999999998] | 9 /9 | 1 | .13611516156427778 |

K15's real upper-envelope switches occur at rho=1.217804157070469 and
1.7536630940274902. The low-weight D1 fleet supports the first interval, the
common C-stage component line the middle, and the high-weight D2 fleet the last.
The worst certified quality band occurs at the first intersection, not at an
original sample. A single fixed C-stage fleet has worst regret upper
.0082385919783785; switching among the three known feasible options reduces
that bound to .0023562818631971206. Neither fact proves full Pareto completeness.

UC-B20 has one identical G/p line in all six observations. A named fixed fleet
from that line has the stated numerical-width quality guarantee over the full
range. This is a continuous stability conclusion from the archive and qualified
lower chords, rather than a new solve at every weight.

RB20's supported component switches are .8050204605328328 and1.487745188758254.
Its actual low-weight P/PS/B runs remain open, and the largest archive band is at
that low endpoint. The lower-weight PS/B fleet itself has worst regret upper
.015594268604373972 over the entire interval. That fixed-fleet guarantee and
the archive's three supported choices are different statements.

RX35's rho2 B fleet (original owner R137:B3:71) supports the whole archive
envelope; all historical producer runs remain open. Its large .13611516156427778
upper bound on regret reflects unresolved proof/primal quality, not an optimal
tradeoff frontier. At the original unit-weight run's actual rho, the rho2 fleet
has recomputed F=.3365058164688021, against the old unit-weight fleet's
.40327199886285475: a known feasible improvement of .06676618239405259. Both
G and p improve. The original stored U=.4032719988628547, discovery/verification
time and certificate status remain untouched. No archive fleet enters formal
B/C166 startup, hints, cutoff or floor.

Machine sources: analysis/parameter_envelopes.json (exact fractions, all owners,
anchors, chords, critical points and fixed-plan guarantees), parameter_lines.csv,
parameter_intersections.csv, parameter_summary.csv and X35_offline_improvement.json.

## Two-sided value of physical route time

For all four T-pairs every datum except T matches and T2>T1. Their physical
domains are nested. With qualified L_j and feasible U_j,

max(0,L1-U2) <= F*(T1)-F*(T2) <= U1-L2.

| Pair | Original qualified interval | Original width | Guarded interval |
|---|---|---|---|
| B20:3300→5100 | [.28226197612912823,.28226198910913997] | .000000012980011732111052 | [.2822618761281282,.28226208911013995] |
| X20:4800→7200 | [.21052939956455918,.2105294020030558] | .0000000024384966268442554 | [.2105292995635592,.21052950200405582] |
| B35:4800→7200 | [.1112612656599235,.3725316851669952] | .2612704195070717 | [.1112611656589235,.37253178516799523] |
| X35:4200→6300 | [.060085998385418116,.38130342900314945] | .32121743061773134 | [.060085898384418135,.38130352900414943] |

The guarded exact arithmetic and original binary64 records are both retained in
analysis/resource_intervals.json/.csv. The B35/X35 optima improve strictly even
though both source runs remain OPEN, while the magnitude uncertainty is broad.
The smaller pairs locate that value change much more closely. This is change in
the specified weighted objective, not monetary savings or a general resource price.

## Operations across all four pairs

| Pair | G: T1→T2 | p: T1→T2 | Pickup/drop: T1→T2 | Loaded return: T1→T2 | Station total: T1→T2 |
|---|---|---|---|---|---|
| B20 | .216444→.0819181 | .264291→.116555 | 30/30→43/43 | 0→0 | 143→143 |
| X20 | .314652→.206001 | .330673→.228795 | 16/15→22/22 | 1→0 | 64→65 |
| B35 | .285367→.181545 | .306150→.163098 | 41/39→60/57 | 2→3 | 234→233 |
| X35 | .268135→.182550 | .324055→.220722 | 29/28→42/42 | 1→0 | 145→146 |

At-target station counts change 5→7,12→12,10→21 and14→14 respectively; over-target
counts change 3→0,1→0,8→4 and6→1. The X20/X35 counts show why fewer over-target
stations need not mean fewer under-target stations even when G/p improve.
All route-level travel, handling, unload, prefix-peak and duration/T values are
reported together in the physical archive. For example, B35's better objective
coexists with one more returned unit; X35's better objective keeps one more unit
at stations. No optimal-mechanism causality follows from those displayed routes.
Near-full duration utilization alone does not prove a binding constraint at an
unknown optimum. Physical T and computational caps remain distinct.

This entire analysis is offline. New weights, physical production inputs,
Seeds, solver calls, strict B/P pairs and algorithm speed observations: zero.
The two hand-enumerable synthetic qualification fixtures are diagnostic examples,
not independent benchmark inputs. The later fixed B/C166 matrix remains a
separate representation experiment on six already exposed physical inputs.
