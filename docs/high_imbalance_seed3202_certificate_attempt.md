# high_imbalance_seed3202 Certificate Attempt

Date: 2026-06-28

Priority target: `reference/hard_stress/V20_M3/high_imbalance_seed3202.txt`.

Previous best valid evidence:

- mip-light 1200s gap: `0.0317627113992`;
- unresolved intervals include the gamma bands around
  `[0.534375,0.554166666667]` and `[0.554166666667,0.573958333333]`.

This round added an exhaustive portfolio mode and focused interval harness.  The
full 300s exhaustive row did not close:

| row | LB | UB | gap | status |
|---|---:|---:|---:|---|
| exhaustive 300s | 1.61719766358 | 1.74931345205 | 0.0755243654678 | not closed |

Focused interval attempts:

| interval | gamma range | previous LB | focused LB | merge status |
|---|---|---:|---:|---|
| 13 | [0.554166666667,0.573958333333] | 1.73333384706 | 1.06421478404 | diagnostic only |
| 18 | [0.534375,0.554166666667] | 1.71354218039 | 1.06421478404 | diagnostic only |

The focused rows are weaker than the inherited full-frontier evidence and are
not safe to merge.  No V20 certificate is obtained in this round.

Diagnosis: the current focus-only path does not preserve enough parent-ledger
context, and the lower-bound relaxation still permits improving relaxed
solutions in the controlling gamma bands.  The next exact-closure step should
either carry full-ledger inherited bounds into focused solves or implement a
true standalone cutoff-feasibility MIP for the target interval.

