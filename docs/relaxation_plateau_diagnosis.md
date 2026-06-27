# Relaxation Plateau Diagnosis

## Regenerated V12

V12 M2 remains certified with the original paper-core 300s command and native
HGA-TGBC UB:

- objective/LB/UB: `0.718504070755`
- certificate: relaxation-only full-frontier certificate
- unresolved intervals: `0`
- pricing calls: `0`

V12 M1 now certifies under a 1200s paper-core run:

- objective/LB/UB: `0.357200583208`
- runtime: `474.6660521s`
- bound time: `460.8823549s`
- pricing calls: `0`
- certificate: relaxation-only full-frontier certificate

The 300s V12 M1 rows remain noncertified, so the closure is time-budget
sensitive but no longer structurally blocked.

## V20/M3

All six hard-generated V20/M3 rows remain noncertified. The new continuous
vehicle-indexed relaxation is active in these rows, but the relaxation lower
bounds still do not reach the verified incumbent cutoffs. The best observed
V20/M3 improvement is `high_imbalance_seed3202`, whose gap decreased from about
`0.12395` in the previous stress summary to `0.10008` at 300s and `0.08167` at
1200s.

The next bottleneck is stronger large-instance-valid lower bounds. Since
route-mask enumeration is not certifying for V20/M3, future work should target
stronger vehicle-indexed flow/capacity cuts, station residual covers, and
deterministic parallel relaxation.
