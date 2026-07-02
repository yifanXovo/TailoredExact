# moderate_seed3301 Time Profile

`moderate_seed3301` did not certify in this round.

Best solver-final bounded row:

- row: `exact_moderate_seed3301_300s_static30.json`;
- status: `gcap_frontier_not_closed`;
- LB: `0.044391`;
- UB: `0.0491525526647`;
- gap: `0.096872947723`;
- unresolved intervals: `2`.

Longer dynamic/static attempts were externally interrupted and are retained as
noncertified wrapper artifacts. Their checkpoint LB/UB/gap fields are copied
from safe progress logs only and do not make certificate claims.

The remaining blocker is compact fixed-interval MIP closure on low-Gini leaves.
The useful next work is stronger low-Gini domain propagation and root cuts that
improve those leaf MIP bounds before branch-and-cut.
