# Prior PB-C50-S proof obligations (finite read-only reconstruction)

The R122 Seed0 and Seed1 runs remain separate. Available journal times below are upper bounds on when an observation was usable, not an invented internal discovery time. The known own F=0.3723417754990474 is feasible; its optimality is unknown. No prior route, cutoff, bound, basis, tree or cache is an input to Round123.

| Seed | Method | First available F / G / time | Final U | Final L | Final controlling leaf |
|---:|---|---|---:|---:|---|
| 0 | MB-D1 | 0.372341775499047 / 0.0501195841945186 / 34.234000000s | 0.3723417754990474 | 0.356874739941336 | L0.0.0.0 |
| 0 | M-B | 0.372341775499047 / 0.0501195841945186 / 34.485000000s | 0.3723417754990474 | 0.356874739941336 | L0.0.0.0 |
| 0 | ENS-C | 0.372341775499047 / 0.0501195841945186 / 34.515000000s | 0.3723417754990474 | 0.3579807998830059 | L0.0.0.0 |
| 0 | P-GRB | 2.20642097200378 / 0.370773203098519 / 1.516000000s | 0.4259500752940563 | 0.3492206958008561 | complete original compact model |
| 1 | M-B | 0.372341775499047 / 0.0501195841945186 / 34.516000000s | 0.3723417754990474 | 0.3570083339726426 | L0.0.0.0 |
| 1 | ENS-C | 0.372341775499047 / 0.0501195841945186 / 34.625000000s | 0.3723417754990474 | 0.3581617620143908 | L0.0.0.0 |
| 1 | P-GRB | 2.20642097200378 / 0.370773203098519 / 1.469000000s | 0.391780558579282 | 0.3494508596458403 | complete original compact model |
| 1 | MB-D1 | 0.372341775499047 / 0.0501195841945186 / 34.343000000s | 0.3723417754990474 | 0.3570083339726426 | L0.0.0.0 |

For all integrated Seed0/Seed1 runs the three original atomic splits have the recorded reasons shown in the JSON: the first two retain infeasible right halves as closed improvement regions; the third follows the original AM score. The final improving-domain cover contains two open depth-3 leaves [0,0.046542721937380925] and [0.046542721937380925,0.09308544387476185], the two closed right ancestors, and the analytic cutoff complement. Closed means exclusion of a strict improver under the recorded cutoff, not physical infeasibility of the unrestricted original problem. Replaced ancestors are not additional covering cells.

The global lower endpoint is the minimum of the valid cover and cutoff complement. It is supplied by L0.0.0.0, not by the larger sibling bound. In particular the final own G=0.050119584194518584 lies in L0.0.0.1 and outside the target MIP leaf L0.0.0.0. Absence of an exact-g Start for that target is therefore compatible with a valid global incumbent. The JSON checks every recorded call interval and cutoff against each own final fleet; it does not claim a free mapping into an incompatible leaf.

The journal gives directly replayable fleet/observation availability. Internal first-discovery times, native acceptance of each candidate and the complete internal reason for continued proof effort are not reconstructed where no record exists. The same final objective across runs does not prove optimality. Group08 P keeps its original final U, clocks and recovery waiting; the historical smaller legal witness remains a trajectory fact. No new root/terminal Optimize, fixed-U diagnostic or new lower bound was computed.
