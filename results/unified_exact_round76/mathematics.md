# JDS-C: verified physical closure after JDS-X

The actual preset is `research-round76-vds-physical-closure`. It inherits the
R73 JDS-X constructor and all25 finite decoded inter-route descent seeds, then
closes the best current original physical witness using the R73 insertion and
R75 quantity proposal APIs. It does not implicitly run QDS-X first. The default
presets, exact formulation, native Start mapping and full VD-S proof remain
unchanged. Parsed input must satisfy the inherited symmetric metric guard.

```
routes = best verified witness from JDS-X startup
repeat:
    i = best gain/duration improving unvisited-station insertion(routes)
    q = minimum-F improving served-station quantity change(routes)
    if the sole whole-run deadline was reached: end the whole run
    if neither proposal exists: finish physical closure
    proposal = smaller proposed F of i and q (exact tie favors i)
    candidate = materialize proposal on current routes
    recompute all original physical constraints and original F
    if invalid, prediction differs by >1e-10, or improvement <=1e-12:
        retain prior witness, report verification failure, end closure
    adopt candidate
submit the paid verified best witness to unchanged full VD-S proof
```

The last step occurs only while the global work deadline allows the complete
algorithm to continue. No private component time/Work limit selects a branch.
Experiment watchdogs terminate the whole process; they are not this method's
heuristic decisions. Numerical rejection is an explicit failed experimental
acceptance condition, not an ordinary fallback mechanism.

## Neighborhood and termination scope

R73 considers every legal unvisited single pickup, single drop or equal
pickup/drop pair, on every vehicle and ordered pair of insertion legs, with
all stock/prefix-capacity/handling-duration-feasible positive integer amounts.
For fixed stations and amount the objective is independent of placement;
the helper retains the least-travel feasible placement. It ranks original F
gain per added duration, with its established deterministic convention for
nonpositive added duration. R73's separate exhaustive tests remain enabled.

R75 considers every legal nonzero integer signed-operation change at one
served station, or opposite changes at two currently served stations. It
permits sign changes, deletion when an operation becomes zero, and cross-
vehicle pairs, retaining the other visited stations' relative order. It
selects minimum original F. R75 mathematics.md and its independent exhaustive
tests establish the stock ranges, all affected prefix bounds, exact duration
recalculation and coupled Gini delta. Loaded returns and cumulative pickup
above vehicle capacity retain the original semantics.

Selection between these two proposals is not a minimum-F oracle over their
union: the insertion proposal uses gain/duration. If both return no strict
improvement after a complete pass, neither of the declared neighborhoods has
a strict improving move at the heuristic tolerance. This is neighborhood
exhaustion, not an optimality certificate for BRP. Quantities can delete a
station and permit a later new insertion; there is no cap of V accepted moves.

Final inventories are integer and bounded by station capacities. Every
accepted move decreases deterministically recomputed original F by >1e-12.
Therefore no inventory can recur and the process terminates over a finite
set, apart from the sole global deadline or an explicit numerical rejection.
This gives no useful polynomial-time bound or speed guarantee. Neutral route
relocation, neutral quantity changes and larger neighborhoods are not included.

## Original objective and exactness

The objective remains H/(nS) + lambda*P, with Y=b+drop-pickup, r=Y/D,
S=sum(r), H=sum(i<j)|ri-rj| and the original S=0 convention. The helper
predictions include changes to the denominator, all affected pair distances
and the original weighted absolute deviation. Every adoption is checked with
the original full verifier, including empty departure, single nonzero one-way
service, all load prefixes, stock bounds and travel plus handling duration.
Initial/final JSON witnesses and every operation are persisted for replay.

Heuristic neighborhood restrictions exclude nothing from the exact solver's
feasible domain. Only the verified incumbent changes; full-domain proof and
complete frontier coverage retain their prior scope. The unchanged outer
incumbent threshold is1e-10, so a smaller valid closure gain can leave the
previous outer witness in place. Audits explicitly allow only that case.
Zero requested MIP gaps still give the established numerical certificate,
not a newly implemented strict rational certificate.

This method repairs a demonstrated physical handoff gap. Generic insertion,
quantity repair and their composition are established heuristic ideas; no
theoretical novelty is claimed. Relevant primary literature and differences
from this model are recorded in R74/literature_notes.md and R75/mathematics.md.
Efficiency must be demonstrated separately on the complete algorithm.
